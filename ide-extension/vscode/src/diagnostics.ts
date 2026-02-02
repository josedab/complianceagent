/**
 * Compliance Diagnostics Manager
 */

import * as vscode from 'vscode';
import { ComplianceIssue } from './api';

export class ComplianceDiagnostics {
    private collection: vscode.DiagnosticCollection | null = null;
    private issues: Map<string, ComplianceIssue[]> = new Map();
    private changeCallbacks: (() => void)[] = [];

    setCollection(collection: vscode.DiagnosticCollection): void {
        this.collection = collection;
    }

    onDiagnosticsChange(callback: () => void): void {
        this.changeCallbacks.push(callback);
    }

    private notifyChange(): void {
        for (const callback of this.changeCallbacks) {
            callback();
        }
    }

    /**
     * Update diagnostics for a document
     */
    updateForDocument(uri: vscode.Uri, issues: ComplianceIssue[]): void {
        if (!this.collection) {
            return;
        }

        this.issues.set(uri.toString(), issues);

        const diagnostics = issues.map(issue => {
            const range = new vscode.Range(
                issue.line - 1,
                issue.column,
                issue.line - 1,
                issue.endColumn
            );

            const severity = this.toVscodeSeverity(issue.severity);
            
            const diagnostic = new vscode.Diagnostic(
                range,
                `[${issue.framework}] ${issue.title}: ${issue.description}`,
                severity
            );
            
            diagnostic.code = issue.requirementId;
            diagnostic.source = 'ComplianceAgent';
            
            // Store issue data for quick fix provider
            (diagnostic as any).complianceIssue = issue;

            return diagnostic;
        });

        this.collection.set(uri, diagnostics);
        this.notifyChange();
    }

    /**
     * Clear diagnostics for a document
     */
    clearForDocument(uri: vscode.Uri): void {
        if (this.collection) {
            this.collection.delete(uri);
            this.issues.delete(uri.toString());
            this.notifyChange();
        }
    }

    /**
     * Get total issue count
     */
    getTotalCount(): number {
        let total = 0;
        for (const issues of this.issues.values()) {
            total += issues.length;
        }
        return total;
    }

    /**
     * Get summary of all issues
     */
    getSummary(): any {
        let critical = 0;
        let high = 0;
        let medium = 0;
        let low = 0;
        const allIssues: any[] = [];

        for (const [uri, issues] of this.issues.entries()) {
            for (const issue of issues) {
                switch (issue.severity) {
                    case 'critical': critical++; break;
                    case 'high': high++; break;
                    case 'medium': medium++; break;
                    case 'low': low++; break;
                }
                allIssues.push({
                    ...issue,
                    file: uri
                });
            }
        }

        return {
            total: critical + high + medium + low,
            critical,
            high,
            medium,
            low,
            filesScanned: this.issues.size,
            issues: allIssues.slice(0, 20) // Top 20 issues
        };
    }

    /**
     * Get issues for a document
     */
    getIssuesForDocument(uri: vscode.Uri): ComplianceIssue[] {
        return this.issues.get(uri.toString()) || [];
    }

    /**
     * Convert severity to VS Code diagnostic severity
     */
    private toVscodeSeverity(severity: string): vscode.DiagnosticSeverity {
        switch (severity) {
            case 'critical':
            case 'high':
                return vscode.DiagnosticSeverity.Error;
            case 'medium':
                return vscode.DiagnosticSeverity.Warning;
            case 'low':
                return vscode.DiagnosticSeverity.Information;
            default:
                return vscode.DiagnosticSeverity.Hint;
        }
    }
}
