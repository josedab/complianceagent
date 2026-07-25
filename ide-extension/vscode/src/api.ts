/**
 * ComplianceAgent API client.
 */

import axios, { AxiosInstance } from 'axios';


export interface ComplianceIssue {
    framework: string;
    requirementId: string;
    title: string;
    description: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    line: number;
    column: number;
    endColumn: number;
    file: string;
    quickFix?: string;
    quickFixCode?: string;
}

interface AnalysisResponse {
    diagnostics: Array<{
        range: {
            start: { line: number; character: number };
            end: { line: number; character: number };
        };
        message: string;
        severity: string;
        code: string;
        regulation?: string;
    }>;
}

export interface TeamSuppressionApiResponse {
    id: string;
    rule_id: string;
    pattern?: string | null;
    reason: string;
    created_by: string;
    created_at: string;
    expires_at?: string | null;
    approved: boolean;
    approved_by?: string | null;
    usage_count: number;
}

export interface FeedbackApiRequest {
    type: 'false_positive' | 'false_negative' | 'severity_adjustment' | 'helpful';
    issue: ComplianceIssue;
    user_action: 'suppressed' | 'fixed' | 'ignored' | 'reported';
    context: {
        file: string;
        codeSnippet: string;
        language: string;
    };
    timestamp: string;
}

export interface RuleStatsApiResponse {
    rule_id: string;
    total_detections: number;
    false_positive_rate: number;
    fix_rate: number;
    suppression_rate: number;
    avg_time_to_fix_minutes: number | null;
}

export class ComplianceApiClient {
    private client: AxiosInstance;
    private apiKey: string;

    constructor(endpoint: string, apiKey: string) {
        this.apiKey = apiKey;
        const apiOrigin = endpoint.replace(/\/api\/v1\/?$/, '').replace(/\/+$/, '');
        this.client = axios.create({
            baseURL: apiOrigin,
            timeout: 30000,
            maxContentLength: 5 * 1024 * 1024,
            maxBodyLength: 5 * 1024 * 1024,
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey
            }
        });
    }

    isConfigured(): boolean {
        return this.apiKey.length > 0;
    }

    async analyzeCode(
        code: string,
        language: string,
        frameworks: string[],
        fileUri: string = 'untitled:complianceagent'
    ): Promise<ComplianceIssue[]> {
        const response = await this.client.post<AnalysisResponse>('/api/v1/ide/analyze', {
            uri: fileUri,
            content: code,
            language,
            regulations: frameworks
        });

        return response.data.diagnostics.map((diagnostic) => ({
            framework: diagnostic.regulation || 'GENERAL',
            requirementId: diagnostic.code,
            title: diagnostic.code,
            description: diagnostic.message,
            severity: this.mapSeverity(diagnostic.severity),
            line: diagnostic.range.start.line,
            column: diagnostic.range.start.character,
            endColumn: diagnostic.range.end.character,
            file: fileUri
        }));
    }

    async getQuickFix(
        code: string,
        issue: ComplianceIssue,
        language: string
    ): Promise<string | null> {
        const response = await this.client.post<{ fixed_code: string }>(
            '/api/v1/ide/quickfix',
            {
                code,
                diagnostic_code: issue.requirementId,
                diagnostic_message: issue.description,
                regulation: issue.framework,
                language
            }
        );
        return response.data.fixed_code;
    }

    async reportFalsePositive(issue: ComplianceIssue, reason: string): Promise<void> {
        await this.client.post('/api/v1/ide/feedback', {
            type: 'false_positive',
            issue,
            user_action: 'reported',
            reason
        });
    }

    async requestTeamSuppression(
        issue: ComplianceIssue,
        pattern: string | undefined,
        reason: string
    ): Promise<void> {
        await this.client.post('/api/v1/ide/suppressions', {
            rule_id: issue.requirementId,
            pattern,
            reason
        });
    }

    async getTeamSuppressions(): Promise<TeamSuppressionApiResponse[]> {
        const response = await this.client.get<TeamSuppressionApiResponse[]>(
            '/api/v1/ide/suppressions'
        );
        return response.data;
    }

    async recordTeamSuppressionUsage(suppressionId: string): Promise<void> {
        await this.client.post(`/api/v1/ide/suppressions/${suppressionId}/usage`);
    }

    async submitFeedbackBatch(items: FeedbackApiRequest[]): Promise<void> {
        await this.client.post('/api/v1/ide/feedback/batch', { items });
    }

    async getRuleStatistics(): Promise<RuleStatsApiResponse[]> {
        const response = await this.client.get<RuleStatsApiResponse[]>(
            '/api/v1/ide/stats/rules'
        );
        return response.data;
    }

    private mapSeverity(value: string): ComplianceIssue['severity'] {
        switch (value.toLowerCase()) {
            case 'critical':
            case 'error':
                return 'critical';
            case 'high':
            case 'warning':
                return 'high';
            case 'medium':
            case 'information':
                return 'medium';
            default:
                return 'low';
        }
    }
}
