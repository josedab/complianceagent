/**
 * ComplianceAgent VS Code Extension
 * 
 * Real-time compliance suggestions and quick-fixes for regulated codebases.
 * Enhanced with LSP-like language server, learning, and team suppressions.
 */

import * as vscode from 'vscode';
import { ComplianceScanner } from './scanner';
import { ComplianceDiagnostics } from './diagnostics';
import { QuickFixProvider } from './quickfix';
import { ComplianceApiClient } from './api';
import { ComplianceLanguageServer, createComplianceLanguageServer } from './language-server';
import { EnhancedQuickFixProvider, registerQuickFixCommands } from './enhanced-quickfix';
import { TeamSuppressionsManager, LearningService, registerLearningCommands } from './learning';

let scanner: ComplianceScanner;
let diagnostics: ComplianceDiagnostics;
let apiClient: ComplianceApiClient;
let languageServer: ComplianceLanguageServer;
let enhancedQuickFix: EnhancedQuickFixProvider;
let teamManager: TeamSuppressionsManager;
let learningService: LearningService;

export function activate(context: vscode.ExtensionContext) {
    console.log('ComplianceAgent extension is now active');

    // Initialize components
    const config = vscode.workspace.getConfiguration('complianceagent');
    apiClient = new ComplianceApiClient(
        config.get('apiEndpoint') || 'https://api.complianceagent.ai',
        config.get('apiKey') || ''
    );
    
    // Initialize enhanced components
    languageServer = createComplianceLanguageServer();
    languageServer.setApiClient(apiClient);
    languageServer.setFrameworks(config.get('frameworks') || ['GDPR', 'HIPAA', 'SOC2']);
    
    enhancedQuickFix = new EnhancedQuickFixProvider(apiClient);
    enhancedQuickFix.initialize(context, apiClient);
    
    teamManager = new TeamSuppressionsManager(apiClient);
    teamManager.initialize(apiClient);
    
    learningService = new LearningService(apiClient);
    learningService.initialize(context, apiClient);
    
    diagnostics = new ComplianceDiagnostics();
    scanner = new ComplianceScanner(apiClient, diagnostics, config);

    // Register diagnostics collection
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('complianceagent');
    context.subscriptions.push(diagnosticCollection);
    diagnostics.setCollection(diagnosticCollection);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('complianceagent.scanFile', () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                scanner.scanDocument(editor.document);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('complianceagent.scanWorkspace', async () => {
            await scanner.scanWorkspace();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('complianceagent.showDashboard', () => {
            showDashboard(context);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('complianceagent.configure', () => {
            vscode.commands.executeCommand('workbench.action.openSettings', 'complianceagent');
        })
    );

    // Register code action provider for quick fixes (enhanced version)
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            [
                { language: 'python' },
                { language: 'javascript' },
                { language: 'typescript' },
                { language: 'java' },
                { language: 'go' },
                { language: 'csharp' },
                { language: 'ruby' },
                { language: 'php' }
            ],
            enhancedQuickFix,
            {
                providedCodeActionKinds: EnhancedQuickFixProvider.providedCodeActionKinds
            }
        )
    );
    
    // Register quick fix commands
    registerQuickFixCommands(context, enhancedQuickFix, apiClient);
    
    // Register learning commands
    registerLearningCommands(context, teamManager, learningService);

    // Real-time scanning on document change
    if (config.get('enableRealTimeScanning')) {
        context.subscriptions.push(
            vscode.workspace.onDidChangeTextDocument(event => {
                if (event.contentChanges.length > 0) {
                    // Debounce scanning
                    scanner.scheduleDocumentScan(event.document);
                }
            })
        );

        // Scan on document open
        context.subscriptions.push(
            vscode.workspace.onDidOpenTextDocument(document => {
                scanner.scanDocument(document);
            })
        );
    }

    // Scan currently open documents
    vscode.workspace.textDocuments.forEach(document => {
        scanner.scanDocument(document);
    });

    // Status bar item
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.text = '$(shield) Compliance';
    statusBarItem.tooltip = 'ComplianceAgent - Click to scan';
    statusBarItem.command = 'complianceagent.scanFile';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // Update status bar based on diagnostics
    diagnostics.onDiagnosticsChange(() => {
        const count = diagnostics.getTotalCount();
        if (count > 0) {
            statusBarItem.text = `$(shield) ${count} issues`;
            statusBarItem.backgroundColor = new vscode.ThemeColor(
                'statusBarItem.warningBackground'
            );
        } else {
            statusBarItem.text = '$(shield) Compliant';
            statusBarItem.backgroundColor = undefined;
        }
    });
}

function showDashboard(context: vscode.ExtensionContext) {
    const panel = vscode.window.createWebviewPanel(
        'complianceagentDashboard',
        'ComplianceAgent Dashboard',
        vscode.ViewColumn.One,
        {
            enableScripts: true
        }
    );

    panel.webview.html = getDashboardHtml(diagnostics.getSummary());
}

function getDashboardHtml(summary: any): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ComplianceAgent Dashboard</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        .header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .metric {
            background: var(--vscode-editor-inactiveSelectionBackground);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
        }
        .metric-label {
            font-size: 12px;
            opacity: 0.8;
        }
        .critical { color: #e05d44; }
        .high { color: #fe7d37; }
        .medium { color: #dfb317; }
        .low { color: #97ca00; }
        .issues-list {
            margin-top: 20px;
        }
        .issue {
            padding: 10px;
            margin-bottom: 8px;
            border-left: 3px solid;
            background: var(--vscode-editor-inactiveSelectionBackground);
        }
        .issue.critical { border-color: #e05d44; }
        .issue.high { border-color: #fe7d37; }
        .issue.medium { border-color: #dfb317; }
        .issue-title {
            font-weight: bold;
        }
        .issue-location {
            font-size: 12px;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ ComplianceAgent Dashboard</h1>
    </div>
    
    <div class="metrics">
        <div class="metric">
            <div class="metric-value">${summary.total || 0}</div>
            <div class="metric-label">Total Issues</div>
        </div>
        <div class="metric">
            <div class="metric-value critical">${summary.critical || 0}</div>
            <div class="metric-label">Critical</div>
        </div>
        <div class="metric">
            <div class="metric-value high">${summary.high || 0}</div>
            <div class="metric-label">High</div>
        </div>
        <div class="metric">
            <div class="metric-value medium">${summary.medium || 0}</div>
            <div class="metric-label">Medium</div>
        </div>
        <div class="metric">
            <div class="metric-value">${summary.filesScanned || 0}</div>
            <div class="metric-label">Files Scanned</div>
        </div>
    </div>

    <div class="issues-list">
        <h2>Recent Issues</h2>
        ${summary.issues?.map((issue: any) => `
            <div class="issue ${issue.severity}">
                <div class="issue-title">${issue.title}</div>
                <div class="issue-location">${issue.file}:${issue.line}</div>
            </div>
        `).join('') || '<p>No issues found</p>'}
    </div>
</body>
</html>`;
}

export function deactivate() {
    console.log('ComplianceAgent extension deactivated');
    
    // Cleanup
    if (teamManager) {
        teamManager.dispose();
    }
    if (learningService) {
        learningService.dispose();
    }
}
