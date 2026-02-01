'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  complianceApi,
  regulationsApi,
  repositoriesApi,
  mappingsApi,
  auditApi,
  requirementsApi,
} from '@/lib/api';
import type {
  ComplianceStats,
  FrameworkStatus,
  RecentActivity,
  UpcomingDeadline,
  Regulation,
  Repository,
  ComplianceAction,
  AuditTrailEntry,
  CodebaseMapping,
  Requirement,
} from '@/types';

// Generic hook for API calls with loading and error states
function useApiCall<T>(
  apiCall: () => Promise<{ data: T }>,
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiCall();
      setData(response.data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('An error occurred'));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiCall, ...deps]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

// Dashboard Hooks
export function useDashboardStats() {
  const [stats, setStats] = useState<ComplianceStats | null>(null);
  const [frameworkStatuses, setFrameworkStatuses] = useState<FrameworkStatus[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [deadlines, setDeadlines] = useState<UpcomingDeadline[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, regulationsRes, actionsRes] = await Promise.all([
        complianceApi.getStatus(),
        regulationsApi.list(),
        auditApi.listActions({ status: 'pending' }),
      ]);

      // Transform compliance status response
      const statusData = statusRes.data;
      setStats({
        overall_score: statusData.overall_score ?? 87,
        compliant: statusData.compliant ?? 0,
        partial: statusData.partial ?? 0,
        non_compliant: statusData.non_compliant ?? 0,
        pending: statusData.pending ?? 0,
        trend_percentage: statusData.trend_percentage ?? 2.3,
      });

      // Transform regulations into framework statuses
      const regulations = regulationsRes.data?.items || regulationsRes.data || [];
      const frameworks: FrameworkStatus[] = regulations.map((reg: Regulation) => ({
        framework: reg.framework,
        name: reg.short_name || reg.name,
        status: 'COMPLIANT' as const,
        score: 85 + Math.floor(Math.random() * 15),
        requirements_total: 20,
        requirements_compliant: 17,
      }));
      setFrameworkStatuses(frameworks);

      // Transform recent activity
      const actions = actionsRes.data?.items || actionsRes.data || [];
      const activity: RecentActivity[] = actions.slice(0, 5).map((action: ComplianceAction) => ({
        id: action.id,
        type: 'action_created' as const,
        title: action.title,
        description: action.description,
        timestamp: action.created_at,
        status: action.status,
      }));
      setRecentActivity(activity);

      // Calculate deadlines from regulations
      const now = new Date();
      const deadlineList: UpcomingDeadline[] = regulations
        .filter((reg: Regulation) => reg.effective_date)
        .map((reg: Regulation) => {
          const effectiveDate = new Date(reg.effective_date);
          const daysRemaining = Math.ceil(
            (effectiveDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
          );
          return {
            regulation_id: reg.id,
            regulation_name: reg.name,
            effective_date: reg.effective_date,
            days_remaining: daysRemaining,
            priority: daysRemaining < 30 ? 'critical' : daysRemaining < 90 ? 'high' : 'medium',
          };
        })
        .filter((d: UpcomingDeadline) => d.days_remaining > 0)
        .sort((a: UpcomingDeadline, b: UpcomingDeadline) => a.days_remaining - b.days_remaining)
        .slice(0, 5);
      setDeadlines(deadlineList);

    } catch (err) {
      console.error('Dashboard fetch error:', err);
      setError(err instanceof Error ? err : new Error('Failed to fetch dashboard data'));
      // Set fallback data for demo purposes
      setStats({
        overall_score: 87,
        compliant: 42,
        partial: 8,
        non_compliant: 3,
        pending: 5,
        trend_percentage: 2.3,
      });
      setFrameworkStatuses([
        { framework: 'GDPR', name: 'GDPR', status: 'COMPLIANT', score: 95, requirements_total: 24, requirements_compliant: 23 },
        { framework: 'CCPA', name: 'CCPA', status: 'COMPLIANT', score: 92, requirements_total: 18, requirements_compliant: 17 },
        { framework: 'EU_AI_ACT', name: 'EU AI Act', status: 'PARTIAL_COMPLIANCE', score: 68, requirements_total: 15, requirements_compliant: 10 },
        { framework: 'HIPAA', name: 'HIPAA', status: 'PENDING_REVIEW', score: 45, requirements_total: 22, requirements_compliant: 10 },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  return { stats, frameworkStatuses, recentActivity, deadlines, loading, error, refetch: fetchDashboardData };
}

// Regulations Hooks
export function useRegulations(params?: { jurisdiction?: string; framework?: string }) {
  return useApiCall<Regulation[]>(
    () => regulationsApi.list(params).then(res => ({ data: res.data?.items || res.data || [] })),
    [params?.jurisdiction, params?.framework]
  );
}

export function useRegulation(id: string) {
  return useApiCall<Regulation>(
    () => regulationsApi.get(id),
    [id]
  );
}

export function useRequirements(regulationId?: string) {
  return useApiCall<Requirement[]>(
    () => {
      if (regulationId) {
        return regulationsApi.getRequirements(regulationId).then(res => ({
          data: res.data?.items || res.data || []
        }));
      }
      return requirementsApi.list().then(res => ({
        data: res.data?.items || res.data || []
      }));
    },
    [regulationId]
  );
}

// Repository Hooks
export function useRepositories(profileId?: string) {
  return useApiCall<Repository[]>(
    () => repositoriesApi.list(profileId).then(res => ({ data: res.data?.items || res.data || [] })),
    [profileId]
  );
}

export function useRepository(id: string) {
  return useApiCall<Repository>(
    () => repositoriesApi.get(id),
    [id]
  );
}

// Mapping Hooks
export function useMappings(params?: { repository_id?: string; requirement_id?: string }) {
  return useApiCall<CodebaseMapping[]>(
    () => mappingsApi.list(params).then(res => ({ data: res.data?.items || res.data || [] })),
    [params?.repository_id, params?.requirement_id]
  );
}

// Compliance Actions Hooks
export function useComplianceActions(params?: { status?: string; repository_id?: string }) {
  return useApiCall<ComplianceAction[]>(
    () => auditApi.listActions(params).then(res => ({ data: res.data?.items || res.data || [] })),
    [params?.status, params?.repository_id]
  );
}

export function useComplianceAction(id: string) {
  return useApiCall<ComplianceAction>(
    () => auditApi.getAction(id),
    [id]
  );
}

// Audit Trail Hooks
export function useAuditTrail(params?: { regulation_id?: string; event_type?: string }) {
  return useApiCall<AuditTrailEntry[]>(
    () => auditApi.listTrail(params).then(res => ({ data: res.data?.items || res.data || [] })),
    [params?.regulation_id, params?.event_type]
  );
}

// Mutation hooks
export function useCreateRepository() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const createRepository = async (data: {
    platform: string;
    owner: string;
    name: string;
    profile_id: string;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const response = await repositoriesApi.create(data);
      return response.data;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to create repository');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return { createRepository, loading, error };
}

export function useAnalyzeRepository() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const analyzeRepository = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await repositoriesApi.analyze(id);
      return response.data;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to analyze repository');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return { analyzeRepository, loading, error };
}

export function useUpdateAction() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const updateAction = async (id: string, data: Partial<ComplianceAction>) => {
    setLoading(true);
    setError(null);
    try {
      const response = await auditApi.updateAction(id, data);
      return response.data;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to update action');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return { updateAction, loading, error };
}

export function useGenerateCode() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const generateCode = async (mappingId: string, options?: { include_tests?: boolean }) => {
    setLoading(true);
    setError(null);
    try {
      const response = await complianceApi.generateCode(mappingId, options);
      return response.data;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to generate code');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return { generateCode, loading, error };
}
