/**
 * Enhanced Quick Fix Provider with AI-Powered Code Generation
 * 
 * Provides intelligent code actions including:
 * - Single-issue quick fixes
 * - Bulk fix across file/workspace
 * - AI-generated compliant code
 * - Suppressions (file/line/team level)
 */

import * as vscode from 'vscode';
import { ComplianceApiClient, ComplianceIssue } from './api';

/**
 * Suppression scope levels
 */
export type SuppressionScope = 'line' | 'file' | 'workspace' | 'team';

/**
 * Suppression entry
 */
export interface Suppression {
    ruleId: string;
    scope: SuppressionScope;
    location?: {
        file?: string;
        line?: number;
    };
    reason: string;
    createdBy: string;
    createdAt: Date;
    expiresAt?: Date;
}

/**
 * Code fix result
 */
export interface CodeFixResult {
    success: boolean;
    originalCode: string;
    fixedCode: string;
    explanation: string;
    confidence: number;
}

/**
 * Enhanced Quick Fix Provider
 */
export class EnhancedQuickFixProvider implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix,
        vscode.CodeActionKind.Source.append('fixAll.complianceAgent'),
        vscode.CodeActionKind.Source.append('suppress.complianceAgent')
    ];

    private apiClient: ComplianceApiClient | null = null;
    private suppressions: Map<string, Suppression> = new Map();
    private context: vscode.ExtensionContext | null = null;

    constructor(apiClient?: ComplianceApiClient) {
        this.apiClient = apiClient || null;
    }

    /**
     * Initialize with extension context for storage
     */
    initialize(context: vscode.ExtensionContext, apiClient?: ComplianceApiClient): void {
        this.context = context;
        if (apiClient) {
            this.apiClient = apiClient;
        }
        this.loadSuppressions();
    }

    /**
     * Provide code actions for compliance diagnostics
     */
    provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
    ): vscode.ProviderResult<(vscode.CodeAction | vscode.Command)[]> {
        const actions: vscode.CodeAction[] = [];
        
        // Get compliance diagnostics
        const complianceDiagnostics = context.diagnostics.filter(
            d => d.source === 'ComplianceAgent'
        );

        if (complianceDiagnostics.length === 0) {
            return actions;
        }

        // Single issue fixes
        for (const diagnostic of complianceDiagnostics) {
            const issue = (diagnostic as any).complianceIssue as ComplianceIssue | undefined;
            if (!issue) continue;

            // Check if suppressed
            if (this.isSuppressed(issue, document.uri)) {
                continue;
            }

            // Primary quick fix
            const quickFix = this.createQuickFixAction(document, diagnostic, issue);
            if (quickFix) {
                actions.push(quickFix);
            }

            // AI-powered fix (if API available)
            if (this.apiClient?.isConfigured()) {
                const aiFixAction = this.createAIFixAction(document, diagnostic, issue);
                actions.push(aiFixAction);
            }

            // Suppression actions
            actions.push(...this.createSuppressionActions(document, diagnostic, issue));

            // Learn more action
            actions.push(this.createLearnMoreAction(diagnostic, issue));
        }

        // Bulk actions if multiple issues
        if (complianceDiagnostics.length > 1) {
            actions.push(this.createFixAllInFileAction(document, complianceDiagnostics));
            
            if (this.apiClient?.isConfigured()) {
                actions.push(this.createAIFixAllAction(document, complianceDiagnostics));
            }
        }

        return actions;
    }

    /**
     * Create standard quick fix action
     */
    private createQuickFixAction(
        document: vscode.TextDocument,
        diagnostic: vscode.Diagnostic,
        issue: ComplianceIssue
    ): vscode.CodeAction | null {
        if (!issue.quickFix) {
            return null;
        }

        const action = new vscode.CodeAction(
            `🔧 Fix: ${issue.quickFix}`,
            vscode.CodeActionKind.QuickFix
        );
        action.diagnostics = [diagnostic];
        action.isPreferred = true;

        const edit = new vscode.WorkspaceEdit();
        const fix = this.generateFix(document, issue);
        
        if (fix) {
            edit.replace(document.uri, diagnostic.range, fix.fixedCode);
            action.edit = edit;
        } else if (issue.quickFixCode) {
            edit.replace(document.uri, diagnostic.range, issue.quickFixCode);
            action.edit = edit;
        } else {
            // Add TODO comment if no automatic fix
            const comment = this.getCommentSyntax(document.languageId);
            const line = document.lineAt(diagnostic.range.start.line);
            const todoComment = `${comment} TODO: ${issue.quickFix} [${issue.framework}/${issue.requirementId}]\n`;
            edit.insert(document.uri, new vscode.Position(line.lineNumber, 0), todoComment);
            action.edit = edit;
        }

        return action;
    }

    /**
     * Create AI-powered fix action
     */
    private createAIFixAction(
        document: vscode.TextDocument,
        diagnostic: vscode.Diagnostic,
        issue: ComplianceIssue
    ): vscode.CodeAction {
        const action = new vscode.CodeAction(
            `✨ AI Fix: Generate compliant code`,
            vscode.CodeActionKind.QuickFix
        );
        action.diagnostics = [diagnostic];
        
        action.command = {
            command: 'complianceagent.aiQuickFix',
            title: 'Generate AI Fix',
            arguments: [document.uri, diagnostic.range, issue]
        };

        return action;
    }

    /**
     * Create suppression actions
     */
    private createSuppressionActions(
        document: vscode.TextDocument,
        diagnostic: vscode.Diagnostic,
        issue: ComplianceIssue
    ): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];

        // Suppress for this line
        const suppressLineAction = new vscode.CodeAction(
            `🔇 Suppress for this line`,
            vscode.CodeActionKind.QuickFix
        );
        suppressLineAction.diagnostics = [diagnostic];
        suppressLineAction.command = {
            command: 'complianceagent.suppress',
            title: 'Suppress',
            arguments: [issue, 'line', document.uri, diagnostic.range.start.line]
        };
        actions.push(suppressLineAction);

        // Suppress for this file
        const suppressFileAction = new vscode.CodeAction(
            `🔇 Suppress for this file`,
            vscode.CodeActionKind.QuickFix
        );
        suppressFileAction.diagnostics = [diagnostic];
        suppressFileAction.command = {
            command: 'complianceagent.suppress',
            title: 'Suppress',
            arguments: [issue, 'file', document.uri]
        };
        actions.push(suppressFileAction);

        // Mark as false positive (reports to API)
        const falsePositiveAction = new vscode.CodeAction(
            `⚠️ Mark as false positive`,
            vscode.CodeActionKind.QuickFix
        );
        falsePositiveAction.diagnostics = [diagnostic];
        falsePositiveAction.command = {
            command: 'complianceagent.markFalsePositive',
            title: 'Report False Positive',
            arguments: [issue, document.uri]
        };
        actions.push(falsePositiveAction);

        return actions;
    }

    /**
     * Create learn more action
     */
    private createLearnMoreAction(
        diagnostic: vscode.Diagnostic,
        issue: ComplianceIssue
    ): vscode.CodeAction {
        const action = new vscode.CodeAction(
            `📚 Learn about ${issue.framework} - ${issue.requirementId}`,
            vscode.CodeActionKind.QuickFix
        );
        action.diagnostics = [diagnostic];
        action.command = {
            command: 'vscode.open',
            title: 'Learn More',
            arguments: [
                vscode.Uri.parse(`https://complianceagent.ai/docs/${issue.framework.toLowerCase()}/${issue.requirementId}`)
            ]
        };
        action.isPreferred = false;
        return action;
    }

    /**
     * Create fix all issues in file action
     */
    private createFixAllInFileAction(
        document: vscode.TextDocument,
        diagnostics: vscode.Diagnostic[]
    ): vscode.CodeAction {
        const action = new vscode.CodeAction(
            `🔧 Fix all compliance issues in file (${diagnostics.length})`,
            vscode.CodeActionKind.Source.append('fixAll.complianceAgent')
        );
        action.diagnostics = diagnostics;
        
        const edit = new vscode.WorkspaceEdit();
        
        // Sort by line number descending to avoid position shifts
        const sortedDiagnostics = [...diagnostics].sort(
            (a, b) => b.range.start.line - a.range.start.line
        );
        
        for (const diagnostic of sortedDiagnostics) {
            const issue = (diagnostic as any).complianceIssue as ComplianceIssue | undefined;
            if (issue) {
                const fix = this.generateFix(document, issue);
                if (fix) {
                    edit.replace(document.uri, diagnostic.range, fix.fixedCode);
                }
            }
        }
        
        action.edit = edit;
        return action;
    }

    /**
     * Create AI fix all action
     */
    private createAIFixAllAction(
        document: vscode.TextDocument,
        diagnostics: vscode.Diagnostic[]
    ): vscode.CodeAction {
        const action = new vscode.CodeAction(
            `✨ AI Fix all issues in file`,
            vscode.CodeActionKind.Source.append('fixAll.complianceAgent')
        );
        action.diagnostics = diagnostics;
        action.command = {
            command: 'complianceagent.aiFixAll',
            title: 'AI Fix All',
            arguments: [document.uri, diagnostics]
        };
        return action;
    }

    /**
     * Generate fix for an issue
     */
    private generateFix(
        document: vscode.TextDocument,
        issue: ComplianceIssue
    ): CodeFixResult | null {
        const line = document.lineAt(issue.line - 1);
        const lineText = line.text;
        const language = document.languageId;

        // Pattern-based fixes
        const fixers: Record<string, (text: string, lang: string, issue: ComplianceIssue) => CodeFixResult | null> = {
            // Hardcoded credentials -> env var
            'SOC2-CRED-001': (text, lang) => {
                const envVarSyntax = this.getEnvVarSyntax(lang);
                const match = text.match(/(password|secret|api[_-]?key|token)\s*[=:]\s*['"]([^'"]+)['"]/i);
                if (match) {
                    const varName = match[1].toUpperCase().replace(/-/g, '_');
                    const fixed = text.replace(
                        /['"][^'"]+['"]/,
                        envVarSyntax.replace('$VAR', varName)
                    );
                    return {
                        success: true,
                        originalCode: text,
                        fixedCode: fixed,
                        explanation: `Moved credential to environment variable ${varName}`,
                        confidence: 0.95
                    };
                }
                return null;
            },

            // Logging sensitive data -> mask
            'GDPR-LOG-001': (text) => {
                const fixed = text
                    .replace(/(email)\s*}/gi, '"[REDACTED_EMAIL]"}')
                    .replace(/(password)\s*}/gi, '"[REDACTED]"}')
                    .replace(/\{(.*)(email|password|ssn)(.*)\}/gi, '{$1"[REDACTED]"$3}');
                
                if (fixed !== text) {
                    return {
                        success: true,
                        originalCode: text,
                        fixedCode: fixed,
                        explanation: 'Masked sensitive data in log output',
                        confidence: 0.8
                    };
                }
                return null;
            },

            // Weak crypto -> strong crypto
            'SOC2-CRYPTO-001': (text) => {
                let fixed = text
                    .replace(/\bmd5\s*\(/gi, 'sha256(')
                    .replace(/\bsha1\s*\(/gi, 'sha256(');
                
                if (fixed !== text) {
                    return {
                        success: true,
                        originalCode: text,
                        fixedCode: fixed,
                        explanation: 'Upgraded to SHA-256 hashing',
                        confidence: 0.9
                    };
                }
                return null;
            },

            // HTTP -> HTTPS
            'HIPAA-TRANSMIT-001': (text) => {
                const fixed = text.replace(/http:\/\//g, 'https://');
                if (fixed !== text) {
                    return {
                        success: true,
                        originalCode: text,
                        fixedCode: fixed,
                        explanation: 'Upgraded to HTTPS for secure transmission',
                        confidence: 1.0
                    };
                }
                return null;
            },

            // Card data masking
            'PCI-LOG-001': (text) => {
                const fixed = text.replace(
                    /(card[_-]?number|pan|ccn)/gi,
                    '"****" + lastFour'
                );
                if (fixed !== text) {
                    return {
                        success: true,
                        originalCode: text,
                        fixedCode: fixed,
                        explanation: 'Masked card data, showing only last 4 digits',
                        confidence: 0.85
                    };
                }
                return null;
            }
        };

        const fixer = fixers[issue.requirementId];
        if (fixer) {
            return fixer(lineText, language, issue);
        }

        return null;
    }

    /**
     * Get environment variable syntax for language
     */
    private getEnvVarSyntax(language: string): string {
        const syntaxMap: Record<string, string> = {
            python: "os.environ.get('$VAR')",
            javascript: "process.env.$VAR",
            typescript: "process.env.$VAR",
            java: "System.getenv(\"$VAR\")",
            go: "os.Getenv(\"$VAR\")",
            ruby: "ENV['$VAR']",
            csharp: "Environment.GetEnvironmentVariable(\"$VAR\")",
            php: "getenv('$VAR')"
        };
        return syntaxMap[language] || "process.env.$VAR";
    }

    /**
     * Get comment syntax for language
     */
    private getCommentSyntax(language: string): string {
        const commentMap: Record<string, string> = {
            python: '#',
            javascript: '//',
            typescript: '//',
            java: '//',
            go: '//',
            ruby: '#',
            csharp: '//',
            php: '//',
            sql: '--'
        };
        return commentMap[language] || '//';
    }

    /**
     * Check if issue is suppressed
     */
    private isSuppressed(issue: ComplianceIssue, uri: vscode.Uri): boolean {
        // Check line-level suppression
        const lineKey = `${issue.requirementId}:line:${uri.fsPath}:${issue.line}`;
        if (this.suppressions.has(lineKey)) {
            return true;
        }

        // Check file-level suppression
        const fileKey = `${issue.requirementId}:file:${uri.fsPath}`;
        if (this.suppressions.has(fileKey)) {
            return true;
        }

        // Check workspace-level suppression
        const workspaceKey = `${issue.requirementId}:workspace`;
        if (this.suppressions.has(workspaceKey)) {
            return true;
        }

        return false;
    }

    /**
     * Add a suppression
     */
    public addSuppression(
        issue: ComplianceIssue,
        scope: SuppressionScope,
        uri?: vscode.Uri,
        line?: number,
        reason?: string
    ): void {
        let key: string;
        const suppression: Suppression = {
            ruleId: issue.requirementId,
            scope,
            reason: reason || 'User suppressed',
            createdBy: 'vscode-user',
            createdAt: new Date()
        };

        switch (scope) {
            case 'line':
                if (!uri || line === undefined) return;
                key = `${issue.requirementId}:line:${uri.fsPath}:${line}`;
                suppression.location = { file: uri.fsPath, line };
                break;
            case 'file':
                if (!uri) return;
                key = `${issue.requirementId}:file:${uri.fsPath}`;
                suppression.location = { file: uri.fsPath };
                break;
            case 'workspace':
                key = `${issue.requirementId}:workspace`;
                break;
            case 'team':
                key = `${issue.requirementId}:team`;
                break;
            default:
                return;
        }

        this.suppressions.set(key, suppression);
        this.saveSuppressions();
    }

    /**
     * Remove a suppression
     */
    public removeSuppression(key: string): boolean {
        const result = this.suppressions.delete(key);
        if (result) {
            this.saveSuppressions();
        }
        return result;
    }

    /**
     * Get all suppressions
     */
    public getSuppressions(): Map<string, Suppression> {
        return this.suppressions;
    }

    /**
     * Load suppressions from storage
     */
    private loadSuppressions(): void {
        if (!this.context) return;
        
        const stored = this.context.workspaceState.get<[string, Suppression][]>('suppressions', []);
        this.suppressions = new Map(stored);
    }

    /**
     * Save suppressions to storage
     */
    private saveSuppressions(): void {
        if (!this.context) return;
        
        const data = Array.from(this.suppressions.entries());
        this.context.workspaceState.update('suppressions', data);
    }

    /**
     * Clear all suppressions
     */
    public clearSuppressions(): void {
        this.suppressions.clear();
        this.saveSuppressions();
    }

    /**
     * Get suppression statistics
     */
    public getSuppressionStats(): { total: number; byScope: Record<SuppressionScope, number> } {
        const byScope: Record<SuppressionScope, number> = {
            line: 0,
            file: 0,
            workspace: 0,
            team: 0
        };

        for (const suppression of this.suppressions.values()) {
            byScope[suppression.scope]++;
        }

        return {
            total: this.suppressions.size,
            byScope
        };
    }
}

/**
 * Register quick fix commands
 */
export function registerQuickFixCommands(
    context: vscode.ExtensionContext,
    quickFixProvider: EnhancedQuickFixProvider,
    apiClient: ComplianceApiClient
): void {
    // AI Quick Fix command
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'complianceagent.aiQuickFix',
            async (uri: vscode.Uri, range: vscode.Range, issue: ComplianceIssue) => {
                const document = await vscode.workspace.openTextDocument(uri);
                const code = document.getText(range);
                
                try {
                    const fix = await apiClient.getQuickFix(code, issue, document.languageId);
                    if (fix) {
                        const edit = new vscode.WorkspaceEdit();
                        edit.replace(uri, range, fix);
                        await vscode.workspace.applyEdit(edit);
                        vscode.window.showInformationMessage('AI fix applied successfully');
                    } else {
                        vscode.window.showWarningMessage('Could not generate AI fix');
                    }
                } catch (error) {
                    vscode.window.showErrorMessage(`AI fix failed: ${error}`);
                }
            }
        )
    );

    // AI Fix All command
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'complianceagent.aiFixAll',
            async (uri: vscode.Uri, diagnostics: vscode.Diagnostic[]) => {
                const document = await vscode.workspace.openTextDocument(uri);
                const fullCode = document.getText();
                
                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Generating AI fixes...',
                    cancellable: true
                }, async (progress, token) => {
                    const edit = new vscode.WorkspaceEdit();
                    let fixed = 0;
                    
                    // Sort by line descending to avoid position shifts
                    const sorted = [...diagnostics].sort(
                        (a, b) => b.range.start.line - a.range.start.line
                    );
                    
                    for (const diagnostic of sorted) {
                        if (token.isCancellationRequested) break;
                        
                        const issue = (diagnostic as any).complianceIssue as ComplianceIssue;
                        if (!issue) continue;
                        
                        const code = document.getText(diagnostic.range);
                        
                        try {
                            const fix = await apiClient.getQuickFix(code, issue, document.languageId);
                            if (fix) {
                                edit.replace(uri, diagnostic.range, fix);
                                fixed++;
                            }
                        } catch {
                            // Skip failed fixes
                        }
                        
                        progress.report({ increment: (1 / diagnostics.length) * 100 });
                    }
                    
                    if (fixed > 0) {
                        await vscode.workspace.applyEdit(edit);
                        vscode.window.showInformationMessage(`Applied ${fixed} AI fixes`);
                    } else {
                        vscode.window.showWarningMessage('No fixes could be applied');
                    }
                });
            }
        )
    );

    // Suppress command
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'complianceagent.suppress',
            async (issue: ComplianceIssue, scope: SuppressionScope, uri?: vscode.Uri, line?: number) => {
                const reason = await vscode.window.showInputBox({
                    prompt: 'Reason for suppression (optional)',
                    placeHolder: 'e.g., False positive, handled elsewhere'
                });
                
                quickFixProvider.addSuppression(issue, scope, uri, line, reason || undefined);
                
                vscode.window.showInformationMessage(
                    `Suppressed ${issue.requirementId} at ${scope} level`
                );
                
                // Refresh diagnostics
                vscode.commands.executeCommand('complianceagent.scanFile');
            }
        )
    );

    // Mark false positive command
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'complianceagent.markFalsePositive',
            async (issue: ComplianceIssue, uri: vscode.Uri) => {
                const reason = await vscode.window.showInputBox({
                    prompt: 'Why is this a false positive?',
                    placeHolder: 'Explain why this detection is incorrect'
                });
                
                if (reason) {
                    try {
                        await apiClient.reportFalsePositive(issue, reason);
                        quickFixProvider.addSuppression(issue, 'file', uri, undefined, `False positive: ${reason}`);
                        vscode.window.showInformationMessage('Thank you for the feedback!');
                    } catch (error) {
                        vscode.window.showErrorMessage(`Failed to report: ${error}`);
                    }
                }
            }
        )
    );

    // View suppressions command
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'complianceagent.viewSuppressions',
            () => {
                const stats = quickFixProvider.getSuppressionStats();
                vscode.window.showInformationMessage(
                    `Suppressions: ${stats.total} total (${stats.byScope.line} line, ${stats.byScope.file} file, ${stats.byScope.workspace} workspace)`
                );
            }
        )
    );
}
