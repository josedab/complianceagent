/**
 * Quick Fix Provider for Compliance Issues
 */

import * as vscode from 'vscode';
import { ComplianceIssue } from './api';

export class QuickFixProvider implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix
    ];

    provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
    ): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];

        // Get compliance diagnostics
        const complianceDiagnostics = context.diagnostics.filter(
            d => d.source === 'ComplianceAgent'
        );

        for (const diagnostic of complianceDiagnostics) {
            const issue = (diagnostic as any).complianceIssue as ComplianceIssue | undefined;
            
            if (issue) {
                // Add quick fix action if available
                if (issue.quickFix) {
                    const fixAction = this.createQuickFixAction(document, diagnostic, issue);
                    if (fixAction) {
                        actions.push(fixAction);
                    }
                }

                // Add "Learn more" action
                const learnMoreAction = new vscode.CodeAction(
                    `Learn about ${issue.framework} compliance`,
                    vscode.CodeActionKind.QuickFix
                );
                learnMoreAction.command = {
                    command: 'vscode.open',
                    title: 'Learn More',
                    arguments: [
                        vscode.Uri.parse(`https://complianceagent.ai/docs/${issue.framework.toLowerCase()}`)
                    ]
                };
                learnMoreAction.diagnostics = [diagnostic];
                actions.push(learnMoreAction);

                // Add "Mark as False Positive" action
                const falsePositiveAction = new vscode.CodeAction(
                    'Mark as false positive',
                    vscode.CodeActionKind.QuickFix
                );
                falsePositiveAction.command = {
                    command: 'complianceagent.markFalsePositive',
                    title: 'Mark False Positive',
                    arguments: [issue]
                };
                falsePositiveAction.diagnostics = [diagnostic];
                falsePositiveAction.isPreferred = false;
                actions.push(falsePositiveAction);
            }
        }

        return actions;
    }

    private createQuickFixAction(
        document: vscode.TextDocument,
        diagnostic: vscode.Diagnostic,
        issue: ComplianceIssue
    ): vscode.CodeAction | null {
        const action = new vscode.CodeAction(
            `Fix: ${issue.quickFix}`,
            vscode.CodeActionKind.QuickFix
        );
        action.diagnostics = [diagnostic];
        action.isPreferred = true;

        // Generate quick fix based on issue type
        const edit = new vscode.WorkspaceEdit();
        const line = document.lineAt(issue.line - 1);
        
        // Apply pattern-based fixes
        if (issue.quickFixCode) {
            // Use provided quick fix code
            edit.replace(document.uri, diagnostic.range, issue.quickFixCode);
        } else {
            // Generate fix based on issue type
            const fix = this.generateFix(issue, line.text);
            if (fix) {
                edit.replace(document.uri, line.range, fix);
            } else {
                // If no automatic fix available, add a comment
                const comment = this.getCommentPrefix(document.languageId);
                const commentText = `${comment} TODO: ${issue.quickFix} (${issue.framework} - ${issue.requirementId})\n`;
                edit.insert(document.uri, new vscode.Position(issue.line - 1, 0), commentText);
            }
        }

        action.edit = edit;
        return action;
    }

    private generateFix(issue: ComplianceIssue, lineText: string): string | null {
        // Pattern-based automatic fixes
        
        // Fix: Hardcoded credentials -> environment variable
        if (issue.title.includes('Hardcoded credential') || issue.title.includes('Hardcoded API key')) {
            const match = lineText.match(/(password|api[_-]?key)\s*=\s*['"][^'"]+['"]/i);
            if (match) {
                const varName = match[1].toUpperCase().replace(/-/g, '_');
                return lineText.replace(
                    /(['"][^'"]+['"])/,
                    `os.environ.get('${varName}')`
                );
            }
        }

        // Fix: Logging sensitive data -> mask it
        if (issue.title.includes('Sensitive data in logs')) {
            return lineText
                .replace(/password/gi, '"***REDACTED***"')
                .replace(/email/gi, '"***REDACTED***"')
                .replace(/ssn/gi, '"***REDACTED***"');
        }

        return null;
    }

    private getCommentPrefix(languageId: string): string {
        switch (languageId) {
            case 'python':
                return '#';
            case 'java':
            case 'javascript':
            case 'typescript':
            case 'go':
                return '//';
            default:
                return '//';
        }
    }
}
