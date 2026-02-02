/**
 * ComplianceAgent API Client
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

export interface AnalysisResponse {
    issues: ComplianceIssue[];
    score: number;
    grade: string;
    scannedAt: string;
}

export class ComplianceApiClient {
    private client: AxiosInstance;
    private apiKey: string;

    constructor(endpoint: string, apiKey: string) {
        this.apiKey = apiKey;
        this.client = axios.create({
            baseURL: endpoint,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            }
        });
    }

    /**
     * Check if API client is properly configured
     */
    isConfigured(): boolean {
        return this.apiKey.length > 0;
    }

    /**
     * Analyze code for compliance issues
     */
    async analyzeCode(
        code: string,
        language: string,
        frameworks: string[]
    ): Promise<ComplianceIssue[]> {
        try {
            const response = await this.client.post<AnalysisResponse>('/api/v1/ide/analyze', {
                code,
                language,
                frameworks,
                includeQuickFixes: true
            });
            return response.data.issues;
        } catch (error) {
            console.error('API analysis error:', error);
            return [];
        }
    }

    /**
     * Get quick fix suggestion for an issue
     */
    async getQuickFix(
        code: string,
        issue: ComplianceIssue,
        language: string
    ): Promise<string | null> {
        try {
            const response = await this.client.post<{ fix: string }>('/api/v1/ide/quickfix', {
                code,
                issue,
                language
            });
            return response.data.fix;
        } catch (error) {
            console.error('Quick fix API error:', error);
            return null;
        }
    }

    /**
     * Report a false positive
     */
    async reportFalsePositive(issue: ComplianceIssue, reason: string): Promise<void> {
        try {
            await this.client.post('/api/v1/ide/feedback', {
                type: 'false_positive',
                issue,
                reason
            });
        } catch (error) {
            console.error('Feedback API error:', error);
        }
    }
}
