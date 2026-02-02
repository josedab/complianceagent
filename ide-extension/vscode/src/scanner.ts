/**
 * Compliance Scanner - Analyzes code for compliance issues
 */

import * as vscode from 'vscode';
import { ComplianceApiClient, ComplianceIssue } from './api';
import { ComplianceDiagnostics } from './diagnostics';

export class ComplianceScanner {
    private apiClient: ComplianceApiClient;
    private diagnostics: ComplianceDiagnostics;
    private config: vscode.WorkspaceConfiguration;
    private scanTimeouts: Map<string, NodeJS.Timeout> = new Map();
    private scanDebounceMs = 1000;

    constructor(
        apiClient: ComplianceApiClient,
        diagnostics: ComplianceDiagnostics,
        config: vscode.WorkspaceConfiguration
    ) {
        this.apiClient = apiClient;
        this.diagnostics = diagnostics;
        this.config = config;
    }

    /**
     * Schedule a document scan with debouncing
     */
    scheduleDocumentScan(document: vscode.TextDocument): void {
        const uri = document.uri.toString();
        
        // Clear existing timeout
        const existing = this.scanTimeouts.get(uri);
        if (existing) {
            clearTimeout(existing);
        }

        // Schedule new scan
        const timeout = setTimeout(() => {
            this.scanDocument(document);
            this.scanTimeouts.delete(uri);
        }, this.scanDebounceMs);

        this.scanTimeouts.set(uri, timeout);
    }

    /**
     * Scan a single document for compliance issues
     */
    async scanDocument(document: vscode.TextDocument): Promise<void> {
        // Skip non-code files
        if (!this.shouldScan(document)) {
            return;
        }

        const text = document.getText();
        const language = document.languageId;
        const frameworks = this.config.get<string[]>('frameworks') || ['GDPR', 'HIPAA', 'SOC2'];
        const severityThreshold = this.config.get<string>('severityThreshold') || 'medium';

        try {
            // Use local pattern matching for offline/quick analysis
            const localIssues = this.analyzeLocally(document);
            
            // Optionally call API for deeper analysis
            let apiIssues: ComplianceIssue[] = [];
            if (this.apiClient.isConfigured()) {
                try {
                    apiIssues = await this.apiClient.analyzeCode(text, language, frameworks);
                } catch (error) {
                    console.warn('API analysis failed, using local only:', error);
                }
            }

            // Merge and deduplicate issues
            const allIssues = this.mergeIssues(localIssues, apiIssues);
            
            // Filter by severity
            const filteredIssues = this.filterBySeverity(allIssues, severityThreshold);

            // Update diagnostics
            this.diagnostics.updateForDocument(document.uri, filteredIssues);

        } catch (error) {
            console.error('Document scan failed:', error);
        }
    }

    /**
     * Scan entire workspace
     */
    async scanWorkspace(): Promise<void> {
        const files = await vscode.workspace.findFiles(
            '**/*.{py,js,ts,tsx,jsx,java,go}',
            '**/node_modules/**'
        );

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'ComplianceAgent: Scanning workspace',
            cancellable: true
        }, async (progress, token) => {
            const total = files.length;
            let scanned = 0;

            for (const file of files) {
                if (token.isCancellationRequested) {
                    break;
                }

                const document = await vscode.workspace.openTextDocument(file);
                await this.scanDocument(document);

                scanned++;
                progress.report({
                    increment: (1 / total) * 100,
                    message: `${scanned}/${total} files`
                });
            }
        });
    }

    /**
     * Check if document should be scanned
     */
    private shouldScan(document: vscode.TextDocument): boolean {
        const supportedLanguages = ['python', 'javascript', 'typescript', 'java', 'go'];
        return supportedLanguages.includes(document.languageId);
    }

    /**
     * Perform local pattern-based analysis
     */
    private analyzeLocally(document: vscode.TextDocument): ComplianceIssue[] {
        const issues: ComplianceIssue[] = [];
        const text = document.getText();
        const lines = text.split('\n');

        // Pattern definitions for common compliance issues
        const patterns = [
            // GDPR / Privacy patterns
            {
                pattern: /personal[_-]?data|user[_-]?data|pii/gi,
                check: (line: string, context: string) => {
                    if (!context.includes('encrypt') && !context.includes('hash') && !context.includes('mask')) {
                        return {
                            framework: 'GDPR',
                            title: 'Potential unencrypted personal data',
                            description: 'Personal data should be encrypted at rest and in transit',
                            severity: 'high' as const,
                            quickFix: 'Consider encrypting this data before storage'
                        };
                    }
                    return null;
                }
            },
            {
                pattern: /log(ging)?.*password|console\.log.*email|print.*ssn/gi,
                check: () => ({
                    framework: 'GDPR',
                    title: 'Sensitive data in logs',
                    description: 'Logging personal or sensitive data may violate privacy regulations',
                    severity: 'critical' as const,
                    quickFix: 'Remove or mask sensitive data before logging'
                })
            },
            // HIPAA patterns
            {
                pattern: /patient[_-]?id|medical[_-]?record|health[_-]?info|phi/gi,
                check: (line: string, context: string) => {
                    if (!context.includes('encrypt') && !context.includes('hipaa')) {
                        return {
                            framework: 'HIPAA',
                            title: 'Protected Health Information (PHI) detected',
                            description: 'PHI must be encrypted and access must be logged',
                            severity: 'critical' as const,
                            quickFix: 'Ensure PHI is encrypted and access is audited'
                        };
                    }
                    return null;
                }
            },
            // Security patterns
            {
                pattern: /password\s*=\s*['"][^'"]+['"]/gi,
                check: () => ({
                    framework: 'SOC2',
                    title: 'Hardcoded credential detected',
                    description: 'Credentials should not be hardcoded in source code',
                    severity: 'critical' as const,
                    quickFix: 'Move to environment variable or secrets manager'
                })
            },
            {
                pattern: /api[_-]?key\s*=\s*['"][^'"]+['"]/gi,
                check: () => ({
                    framework: 'SOC2',
                    title: 'Hardcoded API key detected',
                    description: 'API keys should be stored securely, not in code',
                    severity: 'critical' as const,
                    quickFix: 'Move to environment variable or secrets manager'
                })
            },
            // Data retention
            {
                pattern: /delete.*user|remove.*account|purge.*data/gi,
                check: (line: string, context: string) => {
                    if (!context.includes('backup') && !context.includes('archive')) {
                        return {
                            framework: 'GDPR',
                            title: 'Data deletion without backup consideration',
                            description: 'Consider backup/archive strategy for data deletion',
                            severity: 'medium' as const,
                            quickFix: 'Implement proper data retention policy'
                        };
                    }
                    return null;
                }
            },
            // Consent patterns
            {
                pattern: /collect.*email|gather.*data|track.*user/gi,
                check: (line: string, context: string) => {
                    if (!context.includes('consent') && !context.includes('permission') && !context.includes('opt')) {
                        return {
                            framework: 'GDPR',
                            title: 'Data collection without consent check',
                            description: 'Data collection should verify user consent first',
                            severity: 'high' as const,
                            quickFix: 'Add consent verification before data collection'
                        };
                    }
                    return null;
                }
            }
        ];

        // Analyze each line
        lines.forEach((line, index) => {
            // Get context (surrounding lines)
            const contextStart = Math.max(0, index - 5);
            const contextEnd = Math.min(lines.length, index + 5);
            const context = lines.slice(contextStart, contextEnd).join('\n').toLowerCase();

            for (const { pattern, check } of patterns) {
                const matches = line.match(pattern);
                if (matches) {
                    const result = check(line, context);
                    if (result) {
                        const matchIndex = line.search(pattern);
                        issues.push({
                            ...result,
                            line: index + 1,
                            column: matchIndex >= 0 ? matchIndex : 0,
                            endColumn: matchIndex >= 0 ? matchIndex + matches[0].length : line.length,
                            requirementId: `${result.framework}-${issues.length + 1}`,
                            file: document.uri.fsPath
                        });
                    }
                }
            }
        });

        return issues;
    }

    /**
     * Merge local and API issues, removing duplicates
     */
    private mergeIssues(local: ComplianceIssue[], api: ComplianceIssue[]): ComplianceIssue[] {
        const merged = [...local];
        
        for (const apiIssue of api) {
            // Check if similar issue already exists from local analysis
            const duplicate = merged.find(
                m => m.line === apiIssue.line && 
                     m.framework === apiIssue.framework &&
                     Math.abs(m.column - apiIssue.column) < 10
            );
            
            if (!duplicate) {
                merged.push(apiIssue);
            }
        }

        return merged;
    }

    /**
     * Filter issues by severity threshold
     */
    private filterBySeverity(issues: ComplianceIssue[], threshold: string): ComplianceIssue[] {
        const severityOrder = ['low', 'medium', 'high', 'critical'];
        const thresholdIndex = severityOrder.indexOf(threshold);
        
        return issues.filter(issue => {
            const issueIndex = severityOrder.indexOf(issue.severity);
            return issueIndex >= thresholdIndex;
        });
    }
}
