/**
 * Team Suppressions and Learning Service
 * 
 * Manages team-wide suppressions and learns from feedback
 * to improve detection accuracy.
 */

import * as vscode from 'vscode';
import { ComplianceApiClient, ComplianceIssue } from './api';

/**
 * Team suppression from backend
 */
export interface TeamSuppression {
    id: string;
    ruleId: string;
    pattern?: string;
    reason: string;
    createdBy: string;
    createdAt: Date;
    expiresAt?: Date;
    approved: boolean;
    approvedBy?: string;
    usageCount: number;
}

/**
 * Learning feedback entry
 */
export interface LearningFeedback {
    type: 'false_positive' | 'false_negative' | 'severity_adjustment' | 'helpful';
    issue: ComplianceIssue;
    userAction: 'suppressed' | 'fixed' | 'ignored' | 'reported';
    context: {
        file: string;
        codeSnippet: string;
        language: string;
    };
    timestamp: Date;
}

/**
 * Rule effectiveness stats
 */
export interface RuleStats {
    ruleId: string;
    totalDetections: number;
    falsePositiveRate: number;
    fixRate: number;
    suppressionRate: number;
    avgTimeToFix: number;
}

/**
 * Team Suppressions Manager
 */
export class TeamSuppressionsManager {
    private teamSuppressions: Map<string, TeamSuppression> = new Map();
    private apiClient: ComplianceApiClient | null = null;
    private syncInterval: ReturnType<typeof setInterval> | null = null;
    private lastSyncTime: Date | null = null;

    constructor(apiClient?: ComplianceApiClient) {
        this.apiClient = apiClient || null;
    }

    /**
     * Initialize with API client
     */
    initialize(apiClient: ComplianceApiClient): void {
        this.apiClient = apiClient;
        this.startSync();
    }

    /**
     * Start periodic sync with backend
     */
    private startSync(): void {
        // Initial sync
        this.syncFromBackend();
        
        // Sync every 5 minutes
        this.syncInterval = setInterval(() => {
            this.syncFromBackend();
        }, 5 * 60 * 1000);
    }

    /**
     * Stop sync
     */
    dispose(): void {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
        }
    }

    /**
     * Sync suppressions from backend
     */
    async syncFromBackend(): Promise<void> {
        if (!this.apiClient?.isConfigured()) {
            return;
        }

        try {
            const response = await this.fetchTeamSuppressions();
            this.teamSuppressions.clear();
            
            for (const suppression of response) {
                this.teamSuppressions.set(suppression.id, suppression);
            }
            
            this.lastSyncTime = new Date();
            console.log(`Synced ${response.length} team suppressions`);
        } catch (error) {
            console.warn('Failed to sync team suppressions:', error);
        }
    }

    /**
     * Fetch team suppressions from API
     */
    private async fetchTeamSuppressions(): Promise<TeamSuppression[]> {
        // This would call the actual API endpoint
        // For now, return empty array as placeholder
        return [];
    }

    /**
     * Check if issue matches a team suppression
     */
    isTeamSuppressed(issue: ComplianceIssue, code: string): boolean {
        for (const suppression of this.teamSuppressions.values()) {
            if (!suppression.approved) continue;
            
            // Check by rule ID
            if (suppression.ruleId === issue.requirementId) {
                // If pattern specified, check if code matches
                if (suppression.pattern) {
                    try {
                        const regex = new RegExp(suppression.pattern, 'i');
                        if (regex.test(code)) {
                            this.incrementUsage(suppression.id);
                            return true;
                        }
                    } catch {
                        // Invalid regex, skip pattern check
                    }
                } else {
                    this.incrementUsage(suppression.id);
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * Increment usage count for suppression
     */
    private incrementUsage(id: string): void {
        const suppression = this.teamSuppressions.get(id);
        if (suppression) {
            suppression.usageCount++;
        }
    }

    /**
     * Request a new team suppression
     */
    async requestSuppression(
        issue: ComplianceIssue,
        pattern: string | undefined,
        reason: string
    ): Promise<boolean> {
        if (!this.apiClient?.isConfigured()) {
            vscode.window.showWarningMessage('API not configured for team suppressions');
            return false;
        }

        try {
            // This would call the actual API endpoint
            vscode.window.showInformationMessage(
                `Team suppression requested for ${issue.requirementId}. Awaiting approval.`
            );
            return true;
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to request suppression: ${error}`);
            return false;
        }
    }

    /**
     * Get all team suppressions
     */
    getSuppressions(): TeamSuppression[] {
        return Array.from(this.teamSuppressions.values());
    }

    /**
     * Get suppression by ID
     */
    getSuppression(id: string): TeamSuppression | undefined {
        return this.teamSuppressions.get(id);
    }

    /**
     * Get last sync time
     */
    getLastSyncTime(): Date | null {
        return this.lastSyncTime;
    }
}

/**
 * Learning Service - Collects and processes user feedback
 */
export class LearningService {
    private feedbackQueue: LearningFeedback[] = [];
    private ruleStats: Map<string, RuleStats> = new Map();
    private apiClient: ComplianceApiClient | null = null;
    private context: vscode.ExtensionContext | null = null;
    private flushInterval: ReturnType<typeof setInterval> | null = null;

    constructor(apiClient?: ComplianceApiClient) {
        this.apiClient = apiClient || null;
    }

    /**
     * Initialize with context and API client
     */
    initialize(context: vscode.ExtensionContext, apiClient?: ComplianceApiClient): void {
        this.context = context;
        if (apiClient) {
            this.apiClient = apiClient;
        }
        
        this.loadStats();
        this.startFlushInterval();
    }

    /**
     * Start periodic flush of feedback queue
     */
    private startFlushInterval(): void {
        // Flush every minute
        this.flushInterval = setInterval(() => {
            this.flushFeedback();
        }, 60 * 1000);
    }

    /**
     * Stop flush interval
     */
    dispose(): void {
        if (this.flushInterval) {
            clearInterval(this.flushInterval);
            this.flushInterval = null;
        }
        this.flushFeedback();
    }

    /**
     * Record user feedback on an issue
     */
    recordFeedback(
        type: LearningFeedback['type'],
        issue: ComplianceIssue,
        userAction: LearningFeedback['userAction'],
        document: vscode.TextDocument
    ): void {
        const feedback: LearningFeedback = {
            type,
            issue,
            userAction,
            context: {
                file: document.uri.fsPath,
                codeSnippet: this.extractCodeSnippet(document, issue.line),
                language: document.languageId
            },
            timestamp: new Date()
        };

        this.feedbackQueue.push(feedback);
        this.updateLocalStats(issue, userAction);
    }

    /**
     * Extract code snippet around issue
     */
    private extractCodeSnippet(document: vscode.TextDocument, line: number): string {
        const startLine = Math.max(0, line - 3);
        const endLine = Math.min(document.lineCount - 1, line + 3);
        
        const lines: string[] = [];
        for (let i = startLine; i <= endLine; i++) {
            lines.push(document.lineAt(i).text);
        }
        
        return lines.join('\n');
    }

    /**
     * Update local stats for a rule
     */
    private updateLocalStats(issue: ComplianceIssue, action: LearningFeedback['userAction']): void {
        let stats = this.ruleStats.get(issue.requirementId);
        
        if (!stats) {
            stats = {
                ruleId: issue.requirementId,
                totalDetections: 0,
                falsePositiveRate: 0,
                fixRate: 0,
                suppressionRate: 0,
                avgTimeToFix: 0
            };
            this.ruleStats.set(issue.requirementId, stats);
        }

        stats.totalDetections++;

        switch (action) {
            case 'fixed':
                stats.fixRate = (stats.fixRate * (stats.totalDetections - 1) + 1) / stats.totalDetections;
                break;
            case 'suppressed':
                stats.suppressionRate = (stats.suppressionRate * (stats.totalDetections - 1) + 1) / stats.totalDetections;
                break;
            case 'reported':
                stats.falsePositiveRate = (stats.falsePositiveRate * (stats.totalDetections - 1) + 1) / stats.totalDetections;
                break;
        }

        this.saveStats();
    }

    /**
     * Flush feedback to backend
     */
    async flushFeedback(): Promise<void> {
        if (this.feedbackQueue.length === 0) {
            return;
        }

        if (!this.apiClient?.isConfigured()) {
            // Just clear queue if no API
            this.feedbackQueue = [];
            return;
        }

        const batch = [...this.feedbackQueue];
        this.feedbackQueue = [];

        try {
            // This would send feedback to backend
            console.log(`Flushed ${batch.length} feedback items`);
        } catch (error) {
            // Re-queue on failure
            this.feedbackQueue.push(...batch);
            console.warn('Failed to flush feedback:', error);
        }
    }

    /**
     * Get statistics for a rule
     */
    getRuleStats(ruleId: string): RuleStats | undefined {
        return this.ruleStats.get(ruleId);
    }

    /**
     * Get all rule statistics
     */
    getAllStats(): RuleStats[] {
        return Array.from(this.ruleStats.values());
    }

    /**
     * Get high false positive rules
     */
    getHighFalsePositiveRules(threshold: number = 0.3): RuleStats[] {
        return this.getAllStats().filter(s => s.falsePositiveRate > threshold);
    }

    /**
     * Get effectiveness score for a rule (0-1)
     */
    getRuleEffectiveness(ruleId: string): number {
        const stats = this.ruleStats.get(ruleId);
        if (!stats || stats.totalDetections < 5) {
            return 0.5; // Default for new rules
        }

        // Effectiveness = fixRate * (1 - falsePositiveRate)
        return stats.fixRate * (1 - stats.falsePositiveRate);
    }

    /**
     * Should issue be shown based on learning?
     */
    shouldShowIssue(issue: ComplianceIssue): boolean {
        const effectiveness = this.getRuleEffectiveness(issue.requirementId);
        
        // Don't hide if effectiveness unknown
        if (effectiveness === 0.5) {
            return true;
        }

        // Hide rules with <20% effectiveness
        if (effectiveness < 0.2) {
            console.log(`Hiding issue ${issue.requirementId} due to low effectiveness: ${effectiveness}`);
            return false;
        }

        return true;
    }

    /**
     * Adjust severity based on learning
     */
    adjustSeverity(issue: ComplianceIssue): ComplianceIssue['severity'] {
        const stats = this.ruleStats.get(issue.requirementId);
        
        if (!stats || stats.totalDetections < 10) {
            return issue.severity;
        }

        // Downgrade severity if high false positive rate
        if (stats.falsePositiveRate > 0.5) {
            const severities = ['critical', 'high', 'medium', 'low'] as const;
            const currentIndex = severities.indexOf(issue.severity);
            const newIndex = Math.min(currentIndex + 1, severities.length - 1);
            return severities[newIndex];
        }

        // Upgrade severity if high fix rate (indicates important)
        if (stats.fixRate > 0.8 && issue.severity !== 'critical') {
            const severities = ['critical', 'high', 'medium', 'low'] as const;
            const currentIndex = severities.indexOf(issue.severity);
            const newIndex = Math.max(currentIndex - 1, 0);
            return severities[newIndex];
        }

        return issue.severity;
    }

    /**
     * Load stats from storage
     */
    private loadStats(): void {
        if (!this.context) return;

        const stored = this.context.globalState.get<[string, RuleStats][]>('ruleStats', []);
        this.ruleStats = new Map(stored);
    }

    /**
     * Save stats to storage
     */
    private saveStats(): void {
        if (!this.context) return;

        const data = Array.from(this.ruleStats.entries());
        this.context.globalState.update('ruleStats', data);
    }

    /**
     * Clear all stats
     */
    clearStats(): void {
        this.ruleStats.clear();
        this.saveStats();
    }

    /**
     * Export stats as JSON
     */
    exportStats(): string {
        const stats = this.getAllStats();
        return JSON.stringify(stats, null, 2);
    }
}

/**
 * Register learning-related commands
 */
export function registerLearningCommands(
    context: vscode.ExtensionContext,
    teamManager: TeamSuppressionsManager,
    learningService: LearningService
): void {
    // Request team suppression
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'complianceagent.requestTeamSuppression',
            async (issue: ComplianceIssue) => {
                const pattern = await vscode.window.showInputBox({
                    prompt: 'Pattern to match (optional, regex)',
                    placeHolder: 'e.g., test_.*\\.py or leave empty for all'
                });

                const reason = await vscode.window.showInputBox({
                    prompt: 'Reason for team suppression',
                    placeHolder: 'Why should this be suppressed for the entire team?'
                });

                if (reason) {
                    await teamManager.requestSuppression(issue, pattern || undefined, reason);
                }
            }
        )
    );

    // View team suppressions
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'complianceagent.viewTeamSuppressions',
            () => {
                const suppressions = teamManager.getSuppressions();
                
                if (suppressions.length === 0) {
                    vscode.window.showInformationMessage('No team suppressions configured');
                    return;
                }

                const items = suppressions.map(s => ({
                    label: s.ruleId,
                    description: s.reason,
                    detail: `Created by ${s.createdBy}, used ${s.usageCount} times`
                }));

                vscode.window.showQuickPick(items, {
                    placeHolder: 'Team Suppressions'
                });
            }
        )
    );

    // View rule stats
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'complianceagent.viewRuleStats',
            () => {
                const stats = learningService.getAllStats();
                
                if (stats.length === 0) {
                    vscode.window.showInformationMessage('No rule statistics collected yet');
                    return;
                }

                const items = stats
                    .sort((a, b) => b.totalDetections - a.totalDetections)
                    .map(s => ({
                        label: s.ruleId,
                        description: `${s.totalDetections} detections`,
                        detail: `Fix rate: ${(s.fixRate * 100).toFixed(1)}%, FP rate: ${(s.falsePositiveRate * 100).toFixed(1)}%`
                    }));

                vscode.window.showQuickPick(items, {
                    placeHolder: 'Rule Statistics'
                });
            }
        )
    );

    // Export stats
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'complianceagent.exportStats',
            async () => {
                const json = learningService.exportStats();
                
                const doc = await vscode.workspace.openTextDocument({
                    content: json,
                    language: 'json'
                });
                
                await vscode.window.showTextDocument(doc);
            }
        )
    );

    // Sync team suppressions
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'complianceagent.syncTeamSuppressions',
            async () => {
                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Syncing team suppressions...'
                }, async () => {
                    await teamManager.syncFromBackend();
                });
                
                const count = teamManager.getSuppressions().length;
                vscode.window.showInformationMessage(`Synced ${count} team suppressions`);
            }
        )
    );
}
