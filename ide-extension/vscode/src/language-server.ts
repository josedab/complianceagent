/**
 * Compliance Language Server
 * 
 * Provides Language Server Protocol (LSP) support for real-time
 * compliance linting across multiple languages.
 */

import * as vscode from 'vscode';
import { ComplianceApiClient, ComplianceIssue } from './api';

/**
 * Compliance pattern definition
 */
export interface CompliancePattern {
    id: string;
    name: string;
    description: string;
    framework: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    languages: string[];
    pattern: RegExp;
    contextCheck?: (line: string, context: string, match: RegExpMatchArray) => boolean;
    quickFix?: {
        template: string;
        description: string;
    };
    article?: string;
    tags: string[];
}

/**
 * Pattern match result
 */
export interface PatternMatch {
    pattern: CompliancePattern;
    line: number;
    column: number;
    endColumn: number;
    matchedText: string;
    contextLines: string[];
}

/**
 * Language-specific AST analyzer interface
 */
export interface LanguageAnalyzer {
    language: string;
    analyzeFile(content: string): Promise<ComplianceIssue[]>;
}

/**
 * Compliance Language Server provides LSP-like functionality
 * for real-time compliance scanning
 */
export class ComplianceLanguageServer {
    private patterns: CompliancePattern[] = [];
    private languageAnalyzers: Map<string, LanguageAnalyzer> = new Map();
    private documentVersions: Map<string, number> = new Map();
    private pendingAnalysis: Map<string, NodeJS.Timeout> = new Map();
    private analysisDebounceMs = 500;
    private apiClient: ComplianceApiClient | null = null;
    private enabledFrameworks: string[] = ['GDPR', 'HIPAA', 'SOC2', 'PCI-DSS', 'EU-AI-ACT'];

    constructor() {
        this.initializePatterns();
    }

    /**
     * Initialize with API client for enhanced analysis
     */
    setApiClient(client: ComplianceApiClient): void {
        this.apiClient = client;
    }

    /**
     * Set enabled regulatory frameworks
     */
    setFrameworks(frameworks: string[]): void {
        this.enabledFrameworks = frameworks;
    }

    /**
     * Register a language-specific analyzer
     */
    registerLanguageAnalyzer(analyzer: LanguageAnalyzer): void {
        this.languageAnalyzers.set(analyzer.language, analyzer);
    }

    /**
     * Analyze a document for compliance issues
     */
    async analyzeDocument(
        document: vscode.TextDocument,
        options: {
            useApi?: boolean;
            useLocalPatterns?: boolean;
            useAstAnalysis?: boolean;
        } = {}
    ): Promise<ComplianceIssue[]> {
        const { useApi = true, useLocalPatterns = true, useAstAnalysis = true } = options;
        
        const content = document.getText();
        const language = document.languageId;
        const uri = document.uri.toString();
        
        // Track document version to avoid stale results
        const version = document.version;
        this.documentVersions.set(uri, version);

        const allIssues: ComplianceIssue[] = [];

        // Local pattern matching (fast, offline)
        if (useLocalPatterns) {
            const patternIssues = await this.analyzeWithPatterns(document);
            allIssues.push(...patternIssues);
        }

        // Language-specific AST analysis
        if (useAstAnalysis) {
            const analyzer = this.languageAnalyzers.get(language);
            if (analyzer) {
                const astIssues = await analyzer.analyzeFile(content);
                allIssues.push(...astIssues);
            }
        }

        // API-based analysis (deeper, requires connection)
        if (useApi && this.apiClient?.isConfigured()) {
            try {
                const apiIssues = await this.apiClient.analyzeCode(
                    content,
                    language,
                    this.enabledFrameworks
                );
                // Merge API issues, avoiding duplicates
                for (const issue of apiIssues) {
                    if (!this.isDuplicate(issue, allIssues)) {
                        allIssues.push(issue);
                    }
                }
            } catch (error) {
                console.warn('API analysis failed:', error);
            }
        }

        // Check if document version changed during analysis
        if (this.documentVersions.get(uri) !== version) {
            console.log('Document changed during analysis, discarding results');
            return [];
        }

        // Sort by line number and severity
        return this.sortIssues(allIssues);
    }

    /**
     * Schedule incremental analysis for a document change
     */
    scheduleIncrementalAnalysis(
        document: vscode.TextDocument,
        changes: readonly vscode.TextDocumentContentChangeEvent[],
        callback: (issues: ComplianceIssue[]) => void
    ): void {
        const uri = document.uri.toString();

        // Cancel pending analysis
        const pending = this.pendingAnalysis.get(uri);
        if (pending) {
            clearTimeout(pending);
        }

        // Schedule new analysis
        const timeout = setTimeout(async () => {
            this.pendingAnalysis.delete(uri);
            
            // For small changes, only analyze affected lines
            if (this.isSmallChange(changes)) {
                const issues = await this.analyzeChangedLines(document, changes);
                callback(issues);
            } else {
                const issues = await this.analyzeDocument(document);
                callback(issues);
            }
        }, this.analysisDebounceMs);

        this.pendingAnalysis.set(uri, timeout);
    }

    /**
     * Analyze document using regex patterns
     */
    private async analyzeWithPatterns(document: vscode.TextDocument): Promise<ComplianceIssue[]> {
        const issues: ComplianceIssue[] = [];
        const content = document.getText();
        const lines = content.split('\n');
        const language = document.languageId;

        // Get patterns applicable to this language and enabled frameworks
        const applicablePatterns = this.patterns.filter(p => 
            p.languages.includes(language) || p.languages.includes('*')
        ).filter(p => 
            this.enabledFrameworks.includes(p.framework)
        );

        for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
            const line = lines[lineIndex];
            
            // Skip comments and empty lines
            if (this.isCommentOrEmpty(line, language)) {
                continue;
            }

            // Get context for smarter detection
            const contextStart = Math.max(0, lineIndex - 5);
            const contextEnd = Math.min(lines.length, lineIndex + 5);
            const context = lines.slice(contextStart, contextEnd).join('\n');

            for (const pattern of applicablePatterns) {
                const matches = line.matchAll(new RegExp(pattern.pattern, 'gi'));
                
                for (const match of matches) {
                    // Apply context check if defined
                    if (pattern.contextCheck && !pattern.contextCheck(line, context, match)) {
                        continue;
                    }

                    const column = match.index || 0;
                    const matchedText = match[0];

                    issues.push({
                        framework: pattern.framework,
                        requirementId: pattern.id,
                        title: pattern.name,
                        description: pattern.description,
                        severity: pattern.severity,
                        line: lineIndex + 1,
                        column,
                        endColumn: column + matchedText.length,
                        file: document.uri.fsPath,
                        quickFix: pattern.quickFix?.description,
                        quickFixCode: pattern.quickFix?.template
                    });
                }
            }
        }

        return issues;
    }

    /**
     * Analyze only changed lines for incremental updates
     */
    private async analyzeChangedLines(
        document: vscode.TextDocument,
        changes: readonly vscode.TextDocumentContentChangeEvent[]
    ): Promise<ComplianceIssue[]> {
        const issues: ComplianceIssue[] = [];
        const content = document.getText();
        const lines = content.split('\n');
        const language = document.languageId;

        // Get affected line ranges
        const affectedLines = new Set<number>();
        for (const change of changes) {
            if ('range' in change) {
                const startLine = change.range.start.line;
                const endLine = change.range.end.line + (change.text.split('\n').length - 1);
                for (let i = Math.max(0, startLine - 2); i <= Math.min(lines.length - 1, endLine + 2); i++) {
                    affectedLines.add(i);
                }
            }
        }

        const applicablePatterns = this.patterns.filter(p => 
            p.languages.includes(language) || p.languages.includes('*')
        ).filter(p => 
            this.enabledFrameworks.includes(p.framework)
        );

        for (const lineIndex of affectedLines) {
            const line = lines[lineIndex];
            if (!line || this.isCommentOrEmpty(line, language)) {
                continue;
            }

            const contextStart = Math.max(0, lineIndex - 5);
            const contextEnd = Math.min(lines.length, lineIndex + 5);
            const context = lines.slice(contextStart, contextEnd).join('\n');

            for (const pattern of applicablePatterns) {
                const matches = line.matchAll(new RegExp(pattern.pattern, 'gi'));
                
                for (const match of matches) {
                    if (pattern.contextCheck && !pattern.contextCheck(line, context, match)) {
                        continue;
                    }

                    const column = match.index || 0;
                    issues.push({
                        framework: pattern.framework,
                        requirementId: pattern.id,
                        title: pattern.name,
                        description: pattern.description,
                        severity: pattern.severity,
                        line: lineIndex + 1,
                        column,
                        endColumn: column + match[0].length,
                        file: document.uri.fsPath,
                        quickFix: pattern.quickFix?.description,
                        quickFixCode: pattern.quickFix?.template
                    });
                }
            }
        }

        return issues;
    }

    /**
     * Check if a change is small enough for incremental analysis
     */
    private isSmallChange(changes: readonly vscode.TextDocumentContentChangeEvent[]): boolean {
        let totalLength = 0;
        for (const change of changes) {
            totalLength += change.text.length;
            if ('rangeLength' in change) {
                totalLength += change.rangeLength;
            }
        }
        return totalLength < 500; // Arbitrary threshold
    }

    /**
     * Check if line is a comment or empty
     */
    private isCommentOrEmpty(line: string, language: string): boolean {
        const trimmed = line.trim();
        if (!trimmed) return true;

        const commentPrefixes: Record<string, string[]> = {
            python: ['#'],
            javascript: ['//', '/*', '*'],
            typescript: ['//', '/*', '*'],
            java: ['//', '/*', '*'],
            go: ['//', '/*', '*'],
        };

        const prefixes = commentPrefixes[language] || ['//'];
        return prefixes.some(prefix => trimmed.startsWith(prefix));
    }

    /**
     * Check if issue is a duplicate
     */
    private isDuplicate(issue: ComplianceIssue, existing: ComplianceIssue[]): boolean {
        return existing.some(e => 
            e.line === issue.line &&
            e.framework === issue.framework &&
            Math.abs(e.column - issue.column) < 5
        );
    }

    /**
     * Sort issues by severity and line number
     */
    private sortIssues(issues: ComplianceIssue[]): ComplianceIssue[] {
        const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
        return issues.sort((a, b) => {
            const sevDiff = severityOrder[a.severity] - severityOrder[b.severity];
            if (sevDiff !== 0) return sevDiff;
            return a.line - b.line;
        });
    }

    /**
     * Initialize compliance patterns
     */
    private initializePatterns(): void {
        this.patterns = [
            // ========== GDPR Patterns ==========
            {
                id: 'GDPR-PII-001',
                name: 'Unencrypted PII Storage',
                description: 'Personal Identifiable Information should be encrypted at rest',
                framework: 'GDPR',
                severity: 'high',
                languages: ['*'],
                pattern: /(?:personal[_-]?data|user[_-]?data|pii|email|phone|address)\s*[=:]/gi,
                contextCheck: (line, context) => {
                    const lowerContext = context.toLowerCase();
                    return !lowerContext.includes('encrypt') && 
                           !lowerContext.includes('hash') && 
                           !lowerContext.includes('mask');
                },
                quickFix: {
                    description: 'Encrypt before storing',
                    template: '// TODO: Encrypt PII before storage - GDPR Art. 32'
                },
                article: 'Article 32',
                tags: ['pii', 'encryption', 'storage']
            },
            {
                id: 'GDPR-LOG-001',
                name: 'PII in Logs',
                description: 'Logging personal data may violate GDPR principles',
                framework: 'GDPR',
                severity: 'critical',
                languages: ['*'],
                pattern: /(?:log|print|console\.|logger\.).*(?:email|password|ssn|phone|address)/gi,
                quickFix: {
                    description: 'Mask or remove sensitive data from logs',
                    template: '// Redact PII before logging'
                },
                article: 'Article 5(1)(f)',
                tags: ['logging', 'pii']
            },
            {
                id: 'GDPR-CONSENT-001',
                name: 'Data Collection Without Consent Check',
                description: 'Data collection should verify user consent',
                framework: 'GDPR',
                severity: 'high',
                languages: ['*'],
                pattern: /(?:collect|gather|track|store).*(?:data|info|email)/gi,
                contextCheck: (line, context) => {
                    const lowerContext = context.toLowerCase();
                    return !lowerContext.includes('consent') && 
                           !lowerContext.includes('permission') && 
                           !lowerContext.includes('opt');
                },
                quickFix: {
                    description: 'Add consent verification',
                    template: 'if (hasUserConsent()) { /* data collection */ }'
                },
                article: 'Article 6',
                tags: ['consent', 'collection']
            },
            {
                id: 'GDPR-RETENTION-001',
                name: 'Missing Data Retention Logic',
                description: 'Data should have defined retention periods',
                framework: 'GDPR',
                severity: 'medium',
                languages: ['*'],
                pattern: /(?:save|store|persist).*(?:user|customer|personal)/gi,
                contextCheck: (line, context) => {
                    const lowerContext = context.toLowerCase();
                    return !lowerContext.includes('retention') && 
                           !lowerContext.includes('expire') && 
                           !lowerContext.includes('ttl');
                },
                quickFix: {
                    description: 'Add retention policy',
                    template: '// TODO: Define data retention period per GDPR Art. 5(1)(e)'
                },
                article: 'Article 5(1)(e)',
                tags: ['retention', 'storage']
            },
            {
                id: 'GDPR-ERASURE-001',
                name: 'Incomplete Data Erasure',
                description: 'User data deletion must be complete across all systems',
                framework: 'GDPR',
                severity: 'high',
                languages: ['*'],
                pattern: /(?:delete|remove|erase).*(?:user|account|data)/gi,
                contextCheck: (line, context) => {
                    const lowerContext = context.toLowerCase();
                    return !lowerContext.includes('cascade') && 
                           !lowerContext.includes('all') && 
                           !lowerContext.includes('backup');
                },
                quickFix: {
                    description: 'Ensure cascade deletion',
                    template: '// TODO: Implement right to erasure across all systems'
                },
                article: 'Article 17',
                tags: ['erasure', 'right-to-be-forgotten']
            },

            // ========== HIPAA Patterns ==========
            {
                id: 'HIPAA-PHI-001',
                name: 'Unprotected PHI',
                description: 'Protected Health Information must be encrypted and access-controlled',
                framework: 'HIPAA',
                severity: 'critical',
                languages: ['*'],
                pattern: /(?:patient[_-]?id|medical[_-]?record|health[_-]?info|diagnosis|treatment|phi)/gi,
                contextCheck: (line, context) => {
                    const lowerContext = context.toLowerCase();
                    return !lowerContext.includes('encrypt') && !lowerContext.includes('protected');
                },
                quickFix: {
                    description: 'Apply PHI encryption',
                    template: 'encryptPHI(data)'
                },
                article: '164.312(a)(2)(iv)',
                tags: ['phi', 'encryption', 'health']
            },
            {
                id: 'HIPAA-ACCESS-001',
                name: 'PHI Access Without Audit',
                description: 'PHI access must be logged for audit trail',
                framework: 'HIPAA',
                severity: 'critical',
                languages: ['*'],
                pattern: /(?:get|read|access|fetch).*(?:patient|medical|health|phi)/gi,
                contextCheck: (line, context) => {
                    const lowerContext = context.toLowerCase();
                    return !lowerContext.includes('audit') && 
                           !lowerContext.includes('log') && 
                           !lowerContext.includes('track');
                },
                quickFix: {
                    description: 'Add audit logging',
                    template: 'auditLog.recordAccess(userId, recordId)'
                },
                article: '164.312(b)',
                tags: ['audit', 'access-control']
            },
            {
                id: 'HIPAA-TRANSMIT-001',
                name: 'Unencrypted PHI Transmission',
                description: 'PHI must be encrypted during transmission',
                framework: 'HIPAA',
                severity: 'critical',
                languages: ['*'],
                pattern: /http:\/\/.*(?:patient|medical|health)/gi,
                quickFix: {
                    description: 'Use HTTPS for PHI transmission',
                    template: 'https://'
                },
                article: '164.312(e)(1)',
                tags: ['transmission', 'encryption']
            },

            // ========== SOC2 / Security Patterns ==========
            {
                id: 'SOC2-CRED-001',
                name: 'Hardcoded Credentials',
                description: 'Credentials must not be hardcoded in source code',
                framework: 'SOC2',
                severity: 'critical',
                languages: ['*'],
                pattern: /(?:password|secret|api[_-]?key|token)\s*[=:]\s*['"][^'"]{8,}['"]/gi,
                quickFix: {
                    description: 'Use environment variables',
                    template: 'process.env.SECRET_NAME'
                },
                tags: ['credentials', 'secrets']
            },
            {
                id: 'SOC2-SQL-001',
                name: 'Potential SQL Injection',
                description: 'Use parameterized queries to prevent SQL injection',
                framework: 'SOC2',
                severity: 'critical',
                languages: ['python', 'javascript', 'typescript', 'java'],
                pattern: /(?:execute|query|raw).*\+.*(?:input|request|params|user)/gi,
                quickFix: {
                    description: 'Use parameterized query',
                    template: 'db.query("SELECT * FROM users WHERE id = ?", [userId])'
                },
                tags: ['sql-injection', 'security']
            },
            {
                id: 'SOC2-CRYPTO-001',
                name: 'Weak Cryptography',
                description: 'MD5 and SHA1 are not recommended for security',
                framework: 'SOC2',
                severity: 'high',
                languages: ['*'],
                pattern: /(?:md5|sha1)\s*\(/gi,
                quickFix: {
                    description: 'Use SHA-256 or stronger',
                    template: 'sha256('
                },
                tags: ['cryptography', 'hashing']
            },
            {
                id: 'SOC2-EVAL-001',
                name: 'Dangerous eval() Usage',
                description: 'eval() can execute arbitrary code and is a security risk',
                framework: 'SOC2',
                severity: 'critical',
                languages: ['python', 'javascript', 'typescript'],
                pattern: /\beval\s*\(/gi,
                quickFix: {
                    description: 'Remove eval() usage',
                    template: '// Use safer alternatives like JSON.parse()'
                },
                tags: ['code-injection', 'security']
            },

            // ========== PCI-DSS Patterns ==========
            {
                id: 'PCI-CARD-001',
                name: 'Credit Card Data Storage',
                description: 'Full card numbers should not be stored unencrypted',
                framework: 'PCI-DSS',
                severity: 'critical',
                languages: ['*'],
                pattern: /(?:card[_-]?number|credit[_-]?card|ccn|pan)\s*[=:]/gi,
                contextCheck: (line, context) => {
                    const lowerContext = context.toLowerCase();
                    return !lowerContext.includes('encrypt') && 
                           !lowerContext.includes('token') &&
                           !lowerContext.includes('mask');
                },
                quickFix: {
                    description: 'Tokenize card data',
                    template: 'tokenizeCard(cardNumber)'
                },
                article: 'Requirement 3.4',
                tags: ['card-data', 'payment']
            },
            {
                id: 'PCI-CVV-001',
                name: 'CVV Storage Prohibited',
                description: 'CVV/CVC must never be stored',
                framework: 'PCI-DSS',
                severity: 'critical',
                languages: ['*'],
                pattern: /(?:cvv|cvc|cvv2|cvc2|security[_-]?code)\s*[=:]\s*(?!null|undefined|"")/gi,
                quickFix: {
                    description: 'Remove CVV storage',
                    template: '// CVV must not be stored - PCI-DSS Req 3.2'
                },
                article: 'Requirement 3.2',
                tags: ['cvv', 'payment']
            },
            {
                id: 'PCI-LOG-001',
                name: 'Card Data in Logs',
                description: 'Card data must not appear in logs',
                framework: 'PCI-DSS',
                severity: 'critical',
                languages: ['*'],
                pattern: /(?:log|print|console).*(?:card|pan|ccn)/gi,
                quickFix: {
                    description: 'Mask card data in logs',
                    template: 'logger.info("Card: ****" + lastFour)'
                },
                article: 'Requirement 3.3',
                tags: ['logging', 'card-data']
            },

            // ========== EU AI Act Patterns ==========
            {
                id: 'EUAI-EXPLAIN-001',
                name: 'AI Decision Without Explanation',
                description: 'AI decisions should be explainable',
                framework: 'EU-AI-ACT',
                severity: 'high',
                languages: ['python'],
                pattern: /(?:model\.predict|classifier\.predict|\.fit|\.train)/gi,
                contextCheck: (line, context) => {
                    const lowerContext = context.toLowerCase();
                    return !lowerContext.includes('explain') && 
                           !lowerContext.includes('interpret') &&
                           !lowerContext.includes('shap') &&
                           !lowerContext.includes('lime');
                },
                quickFix: {
                    description: 'Add explainability',
                    template: 'explainer = shap.Explainer(model)'
                },
                article: 'Article 13',
                tags: ['ai', 'explainability']
            },
            {
                id: 'EUAI-BIAS-001',
                name: 'Missing Bias Check',
                description: 'AI systems should check for bias',
                framework: 'EU-AI-ACT',
                severity: 'high',
                languages: ['python'],
                pattern: /(?:train_test_split|fit|train).*(?:data|dataset)/gi,
                contextCheck: (line, context) => {
                    const lowerContext = context.toLowerCase();
                    return !lowerContext.includes('fairness') && 
                           !lowerContext.includes('bias') &&
                           !lowerContext.includes('demographic');
                },
                quickFix: {
                    description: 'Add bias detection',
                    template: '# TODO: Implement bias testing per EU AI Act Art. 10'
                },
                article: 'Article 10',
                tags: ['ai', 'bias', 'fairness']
            },
            {
                id: 'EUAI-HUMAN-001',
                name: 'High-Risk AI Without Human Oversight',
                description: 'High-risk AI systems require human oversight mechanisms',
                framework: 'EU-AI-ACT',
                severity: 'critical',
                languages: ['python'],
                pattern: /(?:automate|autonomous|auto_approve|auto_decision)/gi,
                contextCheck: (line, context) => {
                    const lowerContext = context.toLowerCase();
                    return !lowerContext.includes('human') && 
                           !lowerContext.includes('review') &&
                           !lowerContext.includes('approval');
                },
                quickFix: {
                    description: 'Add human oversight',
                    template: 'if (requiresHumanReview(decision)) await getHumanApproval()'
                },
                article: 'Article 14',
                tags: ['ai', 'human-oversight']
            }
        ];
    }

    /**
     * Get all patterns
     */
    getPatterns(): CompliancePattern[] {
        return this.patterns;
    }

    /**
     * Add a custom pattern
     */
    addPattern(pattern: CompliancePattern): void {
        this.patterns.push(pattern);
    }

    /**
     * Remove a pattern by ID
     */
    removePattern(id: string): boolean {
        const index = this.patterns.findIndex(p => p.id === id);
        if (index >= 0) {
            this.patterns.splice(index, 1);
            return true;
        }
        return false;
    }

    /**
     * Get patterns by framework
     */
    getPatternsByFramework(framework: string): CompliancePattern[] {
        return this.patterns.filter(p => p.framework === framework);
    }

    /**
     * Get statistics about patterns
     */
    getPatternStats(): { total: number; byFramework: Record<string, number>; bySeverity: Record<string, number> } {
        const byFramework: Record<string, number> = {};
        const bySeverity: Record<string, number> = {};

        for (const pattern of this.patterns) {
            byFramework[pattern.framework] = (byFramework[pattern.framework] || 0) + 1;
            bySeverity[pattern.severity] = (bySeverity[pattern.severity] || 0) + 1;
        }

        return {
            total: this.patterns.length,
            byFramework,
            bySeverity
        };
    }
}

/**
 * Factory function for creating language server
 */
export function createComplianceLanguageServer(): ComplianceLanguageServer {
    return new ComplianceLanguageServer();
}
