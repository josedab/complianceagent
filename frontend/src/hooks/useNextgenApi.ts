'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  testingApi,
  architectureAdvisorApi,
  driftDetectionApi,
  costCalculatorApi,
  evidenceVaultApi,
  federatedIntelApi,
  marketplaceAppApi,
  industryPacksApi,
  complianceSandboxApi,
  nlQueryApi,
  multiLlmApi,
  impactTimelineApi,
  auditAutopilotApi,
  policySdkApi,
} from '@/lib/api'
import type {
  TestSuiteResult,
  ComplianceTestPattern,
  FrameworkDetectionResult,
  TestValidationResult,
  DesignReviewResult,
  ArchitectureScore,
  DriftBaseline,
  DriftReport,
  CostPrediction,
  ROISummary,
  EvidenceItem,
  AuditReport,
  AuditorSession,
  ComplianceThreat,
  IndustryBenchmark,
  MarketplaceListing,
  AppInstallation,
  IndustryPack,
  SandboxScenario,
  SandboxEnvironment,
  ControlFramework,
  QueryResult,
  QueryHistoryItem,
  ConsensusResult,
  ProviderInfo,
  MultiLLMConfig,
  TimelineView,
  RemediationTask,
  GapAnalysis,
  EvidencePackage,
  ReadinessReport,
  PolicyDefinition,
  PolicyValidation,
  MarketplaceEntry,
  SDKInfo,
} from '@/types/nextgen'

// Generic hook for API calls with loading/error states
function useApiCall<T>(
  apiCall: () => Promise<{ data: T }>,
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiCall()
      setData(response.data)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('An error occurred'))
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiCall, ...deps])

  useEffect(() => {
    refetch()
  }, [refetch])

  return { data, loading, error, refetch }
}

// Generic mutation hook
function useMutation<TInput, TOutput>(
  mutationFn: (input: TInput) => Promise<{ data: TOutput }>
) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const mutate = async (input: TInput): Promise<TOutput> => {
    setLoading(true)
    setError(null)
    try {
      const response = await mutationFn(input)
      return response.data
    } catch (err) {
      const e = err instanceof Error ? err : new Error('Mutation failed')
      setError(e)
      throw e
    } finally {
      setLoading(false)
    }
  }

  return { mutate, loading, error }
}

// ─── Compliance Testing Suite Hooks ─────────────────────────────────────────

export function useTestPatterns(regulation?: string, category?: string) {
  return useApiCall<ComplianceTestPattern[]>(
    () => testingApi.listPatterns({ regulation, category })
      .then(res => ({ data: res.data || [] })),
    [regulation, category]
  )
}

export function useGenerateTestSuite() {
  return useMutation<
    { regulation: string; framework?: string; target_files?: string[]; pattern_ids?: string[] },
    TestSuiteResult
  >(testingApi.generateSuite)
}

export function useDetectFrameworks() {
  return useMutation<
    { repo: string; files?: string[] },
    FrameworkDetectionResult
  >(testingApi.detectFrameworks)
}

export function useValidateTests() {
  return useMutation<string, TestValidationResult>(
    (suiteId) => testingApi.validateTests(suiteId)
  )
}

// ─── Architecture Advisor Hooks ─────────────────────────────────────────────

export function useArchitecturePatterns() {
  return useApiCall<Array<{ type: string; name: string; compliance_notes: string }>>(
    () => architectureAdvisorApi.listPatterns(),
    []
  )
}

export function useAnalyzeArchitecture() {
  return useMutation<
    { repo: string; files?: string[]; regulations?: string[] },
    DesignReviewResult
  >(architectureAdvisorApi.analyze)
}

export function useArchitectureScore(repo: string) {
  return useApiCall<ArchitectureScore>(
    () => architectureAdvisorApi.getScore(repo),
    [repo]
  )
}

// ─── Drift Detection Hooks ──────────────────────────────────────────────────

export function useDriftReport(repo: string) {
  return useApiCall<DriftReport>(
    () => driftDetectionApi.getReport(repo),
    [repo]
  )
}

export function useDriftAlerts() {
  return useApiCall<Array<{ channel: string; status: string }>>(
    () => driftDetectionApi.getAlerts(),
    []
  )
}

export function useCaptureBaseline() {
  return useMutation<
    { repo: string; branch?: string },
    DriftBaseline
  >(driftDetectionApi.captureBaseline)
}

// ─── Cost Calculator Hooks ──────────────────────────────────────────────────

export function useCostPrediction() {
  return useMutation<
    { regulation: string; complexity?: string; team_size?: number },
    CostPrediction
  >(costCalculatorApi.predict)
}

export function useROICalculation() {
  return useMutation<
    { regulation: string },
    ROISummary
  >(costCalculatorApi.calculateROI)
}

export function useCostHistory() {
  return useApiCall<CostPrediction[]>(
    () => costCalculatorApi.getHistory().then(res => ({ data: res.data || [] })),
    []
  )
}

// ─── Evidence Vault Hooks ───────────────────────────────────────────────────

export function useEvidence(framework?: ControlFramework) {
  return useApiCall<EvidenceItem[]>(
    () => evidenceVaultApi.getEvidence(framework ? { framework } : undefined)
      .then(res => ({ data: res.data || [] })),
    [framework]
  )
}

export function useAuditReport(framework: ControlFramework) {
  return useApiCall<AuditReport>(
    () => evidenceVaultApi.generateReport(framework),
    [framework]
  )
}

export function useCreateAuditorSession() {
  return useMutation<
    { auditor_email: string; auditor_name: string },
    AuditorSession
  >(evidenceVaultApi.createAuditorSession)
}

export function useVerifyChain(framework: ControlFramework) {
  return useApiCall<{ verified: boolean }>(
    () => evidenceVaultApi.verifyChain(framework),
    [framework]
  )
}

// ─── Federated Intelligence Hooks ───────────────────────────────────────────

export function useThreatFeed() {
  return useApiCall<ComplianceThreat[]>(
    () => federatedIntelApi.getThreatFeed().then(res => ({ data: res.data || [] })),
    []
  )
}

export function useIndustryBenchmarks() {
  return useApiCall<Record<string, IndustryBenchmark>>(
    () => federatedIntelApi.getBenchmarks(),
    []
  )
}

export function useNetworkStats() {
  return useApiCall<{ total_members: number; total_threats: number; total_patterns: number }>(
    () => federatedIntelApi.getNetworkStats(),
    []
  )
}

// ─── Marketplace Hooks ──────────────────────────────────────────────────────

export function useMarketplaceListing() {
  return useApiCall<MarketplaceListing>(
    () => marketplaceAppApi.getListingInfo(),
    []
  )
}

export function useMarketplaceInstallations() {
  return useApiCall<AppInstallation[]>(
    () => marketplaceAppApi.getInstallations().then(res => ({ data: res.data || [] })),
    []
  )
}

// ─── Industry Packs Hooks ───────────────────────────────────────────────────

export function useIndustryPacks() {
  return useApiCall<IndustryPack[]>(
    () => industryPacksApi.listPacks().then(res => ({ data: res.data || [] })),
    []
  )
}

export function useProvisionPack() {
  return useMutation<string, { regulations_activated: number; policies_created: number }>(
    (vertical) => industryPacksApi.provisionPack(vertical)
  )
}

// ─── Compliance Sandbox Hooks ───────────────────────────────────────────────

export function useSandboxScenarios() {
  return useApiCall<SandboxScenario[]>(
    () => complianceSandboxApi.listScenarios().then(res => ({ data: res.data || [] })),
    []
  )
}

export function useCreateSandboxEnvironment() {
  return useMutation<string, SandboxEnvironment>(
    (scenarioId) => complianceSandboxApi.createEnvironment(scenarioId)
  )
}

// ─── Natural Language Query Hooks ───────────────────────────────────────────

export function useNLQuery() {
  return useMutation<
    { query: string; context?: Record<string, unknown> },
    QueryResult
  >(nlQueryApi.query)
}

export function useQueryHistory(limit = 20) {
  return useApiCall<QueryHistoryItem[]>(
    () => nlQueryApi.getHistory(limit).then(res => ({ data: res.data || [] })),
    [limit]
  )
}

export function useQueryFeedback() {
  return useMutation<
    { query_id: string; helpful: boolean },
    { status: string }
  >(nlQueryApi.submitFeedback)
}

// ─── Multi-LLM Consensus Hooks ─────────────────────────────────────────────

export function useMultiLLMParse() {
  return useMutation<
    { text: string; framework?: string; strategy?: string },
    ConsensusResult
  >(multiLlmApi.parse)
}

export function useLLMProviders() {
  return useApiCall<ProviderInfo[]>(
    () => multiLlmApi.getProviders().then(res => ({ data: res.data || [] })),
    []
  )
}

export function useMultiLLMConfig() {
  return useApiCall<MultiLLMConfig>(
    () => multiLlmApi.getConfig(),
    []
  )
}

// ─── Impact Timeline Hooks ──────────────────────────────────────────────────

export function useImpactTimeline(framework?: string, jurisdiction?: string) {
  return useApiCall<TimelineView>(
    () => impactTimelineApi.getTimeline({ framework, jurisdiction }),
    [framework, jurisdiction]
  )
}

export function useRemediationTasks(taskStatus?: string) {
  return useApiCall<RemediationTask[]>(
    () => impactTimelineApi.getTasks({ task_status: taskStatus }).then(res => ({ data: res.data || [] })),
    [taskStatus]
  )
}

export function useGenerateTimelineTasks() {
  return useMutation<string, RemediationTask[]>(
    (eventId) => impactTimelineApi.generateTasks(eventId)
  )
}

// ─── Audit Autopilot Hooks ──────────────────────────────────────────────────

export function useGapAnalysis() {
  return useMutation<string, GapAnalysis>(
    (framework) => auditAutopilotApi.runGapAnalysis(framework)
  )
}

export function useEvidencePackage() {
  return useMutation<string, EvidencePackage>(
    (framework) => auditAutopilotApi.generateEvidencePackage(framework)
  )
}

export function useReadinessReport() {
  return useMutation<string, ReadinessReport>(
    (framework) => auditAutopilotApi.generateReadinessReport(framework)
  )
}

// ─── Policy SDK Hooks ───────────────────────────────────────────────────────

export function usePolicies(category?: string, framework?: string) {
  return useApiCall<PolicyDefinition[]>(
    () => policySdkApi.listPolicies({ category, framework }).then(res => ({ data: res.data || [] })),
    [category, framework]
  )
}

export function useValidatePolicy() {
  return useMutation<string, PolicyValidation>(
    (policyId) => policySdkApi.validatePolicy(policyId)
  )
}

export function usePolicyMarketplace(query?: string, category?: string) {
  return useApiCall<MarketplaceEntry[]>(
    () => policySdkApi.searchMarketplace({ query, category }).then(res => ({ data: res.data || [] })),
    [query, category]
  )
}

export function useSDKInfo() {
  return useApiCall<SDKInfo[]>(
    () => policySdkApi.listSDKs().then(res => ({ data: res.data || [] })),
    []
  )
}
