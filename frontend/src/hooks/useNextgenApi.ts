'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
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
  ideAgentApi,
  impactSimulatorApi,
  remediationApi,
  postureScoringApi,
  driftDetectionEnhancedApi,
  evidenceVaultEnhancedApi,
  multiLlmEnhancedApi,
  selfHostedEnhancedApi,
  crossBorderTransferApi,
  stressTestingApi,
  zeroTrustScannerApi,
  complianceTrainingApi,
  aiObservatoryApi,
  regulationTestGenApi,
  sentimentAnalyzerApi,
  incidentPlaybookApi,
  costAttributionApi,
  blockchainAuditApi,
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
  DriftEventRecord,
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
  AuditFrameworkSummary,
  PolicyDefinition,
  PolicyValidation,
  MarketplaceEntry,
  SDKInfo,
  RAGSearchResult,
  FeedbackStats,
  BlastRadiusAnalysis,
  ScenarioComparison,
  RemediationAnalytics,
  ApprovalChain,
  RollbackRecord,
  PostureScore,
  PostureBenchmark,
  PostureScoreHistory,
  DriftTrend,
  CoverageMetrics,
  EvidenceGap,
  ProviderHealthMetrics,
  OfflineBundle,
  AirGapStatus,
  DataFlowRecord,
  TransferReportRecord,
  AdequacyDecisionRecord,
  StressScenario,
  StressTestReportRecord,
  ZeroTrustViolation,
  TrainingModuleRecord,
  DeveloperTrainingProfile,
  AIModelRecord,
  AIObservatoryDashboard,
  RegTestSuite,
  RegulationCoverageRecord,
  RiskHeatmapCellRecord,
  PrioritizationRecord,
  PlaybookRecord,
  IncidentRecord,
  CostDashboardRecord,
  BlockchainStateRecord,
  VerificationResultRecord,
} from '@/types/nextgen'

// Generic hook for API calls with loading/error states
function useApiCall<T>(
  apiCall: () => Promise<{ data: T }>,
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const apiCallRef = useRef(apiCall)

  useEffect(() => {
    apiCallRef.current = apiCall
  }, [apiCall])

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiCallRef.current()
      setData(response.data)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('An error occurred'))
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps])

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

export function useDriftEvents(repo?: string) {
  return useApiCall<DriftEventRecord[]>(
    () => driftDetectionApi.listEvents(repo ? { repo } : undefined)
      .then(res => ({ data: res.data || [] })),
    [repo]
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

export function useAuditFrameworks() {
  return useApiCall<AuditFrameworkSummary[]>(
    () => auditAutopilotApi.listFrameworks().then(res => ({ data: res.data || [] })),
    []
  )
}

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

// ─── IDE Compliance Co-Pilot Hooks ──────────────────────────────────────

export function useRAGSearch() {
  return useMutation<
    { query: string; regulations?: string[]; top_k?: number },
    RAGSearchResult[]
  >(ideAgentApi.ragSearch)
}

export function useFeedbackStats() {
  return useApiCall<FeedbackStats>(
    () => ideAgentApi.getFeedbackStats(),
    []
  )
}

// ─── Impact Simulator Hooks ─────────────────────────────────────────────

export function useBlastRadius(scenarioId: string) {
  return useApiCall<BlastRadiusAnalysis>(
    () => impactSimulatorApi.getBlastRadius(scenarioId),
    [scenarioId]
  )
}

export function useCompareScenarios() {
  return useMutation<
    { scenario_ids: string[] },
    ScenarioComparison
  >(impactSimulatorApi.compareScenarios)
}

// ─── Remediation Workflow Hooks ─────────────────────────────────────────

export function useRemediationAnalytics() {
  return useApiCall<RemediationAnalytics>(
    () => remediationApi.getAnalytics(),
    []
  )
}

export function useCreateApprovalChain() {
  return useMutation<string, ApprovalChain>(
    (workflowId) => remediationApi.createApprovalChain(workflowId)
  )
}

export function useRollbackHistory(workflowId?: string) {
  return useApiCall<RollbackRecord[]>(
    () => remediationApi.getRollbackHistory(workflowId ? { workflow_id: workflowId } : undefined)
      .then(res => ({ data: res.data || [] })),
    [workflowId]
  )
}

// ─── Posture Scoring Hooks ──────────────────────────────────────────────

export function usePostureScore(repo?: string) {
  return useApiCall<PostureScore>(
    () => postureScoringApi.getDynamicScore(repo),
    [repo]
  )
}

export function usePostureBenchmark(industry: string, repo?: string) {
  return useApiCall<PostureBenchmark>(
    () => postureScoringApi.getBenchmark(industry, repo),
    [industry, repo]
  )
}

export function usePostureHistory(repo?: string) {
  return useApiCall<PostureScoreHistory>(
    () => postureScoringApi.getHistory(repo),
    [repo]
  )
}

// ─── Enhanced Drift Detection Hooks ─────────────────────────────────────

export function useDriftTrend(repo: string, period?: string) {
  return useApiCall<DriftTrend>(
    () => driftDetectionEnhancedApi.getTrend(repo, period),
    [repo, period]
  )
}

// ─── Enhanced Evidence Vault Hooks ──────────────────────────────────────

export function useEvidenceCoverage(framework: string) {
  return useApiCall<CoverageMetrics>(
    () => evidenceVaultEnhancedApi.getCoverage(framework),
    [framework]
  )
}

export function useEvidenceGaps(framework: string) {
  return useApiCall<EvidenceGap[]>(
    () => evidenceVaultEnhancedApi.getGaps(framework)
      .then(res => ({ data: res.data || [] })),
    [framework]
  )
}

// ─── Enhanced Multi-LLM Hooks ───────────────────────────────────────────

export function useProviderHealth() {
  return useApiCall<ProviderHealthMetrics[]>(
    () => multiLlmEnhancedApi.getProviderHealth()
      .then(res => ({ data: res.data || [] })),
    []
  )
}

// ─── Enhanced Self-Hosted Hooks ─────────────────────────────────────────

export function useOfflineBundles() {
  return useApiCall<OfflineBundle[]>(
    () => selfHostedEnhancedApi.listOfflineBundles()
      .then(res => ({ data: res.data || [] })),
    []
  )
}

export function useAirGapStatus() {
  return useApiCall<AirGapStatus>(
    () => selfHostedEnhancedApi.getAirGapStatus(),
    []
  )
}

// ═══════════════════════════════════════════════════════════════
// Next-Gen v3 Feature Hooks
// ═══════════════════════════════════════════════════════════════

// ─── Cross-Border Data Transfer ─────────────────────────────────────────

export function useDataFlows(source?: string) {
  return useApiCall<DataFlowRecord[]>(
    () => crossBorderTransferApi.listFlows(source ? { source } : undefined)
      .then(res => ({ data: res.data || [] })),
    [source]
  )
}

export function useTransferReport() {
  return useApiCall<TransferReportRecord>(
    () => crossBorderTransferApi.getReport(),
    []
  )
}

export function useAdequacyDecisions() {
  return useApiCall<AdequacyDecisionRecord[]>(
    () => crossBorderTransferApi.getAdequacyDecisions()
      .then(res => ({ data: res.data || [] })),
    []
  )
}

// ─── Stress Testing ─────────────────────────────────────────

export function useStressScenarios() {
  return useApiCall<StressScenario[]>(
    () => stressTestingApi.listScenarios()
      .then(res => ({ data: res.data || [] })),
    []
  )
}

export function useStressReport() {
  return useApiCall<StressTestReportRecord>(
    () => stressTestingApi.getReport(),
    []
  )
}

// ─── Zero-Trust Scanner ─────────────────────────────────────────

export function useZeroTrustViolations(status?: string) {
  return useApiCall<ZeroTrustViolation[]>(
    () => zeroTrustScannerApi.listViolations(status ? { status } : undefined)
      .then(res => ({ data: res.data || [] })),
    [status]
  )
}

export function useZeroTrustSummary() {
  return useApiCall<Record<string, number>>(
    () => zeroTrustScannerApi.getSummary(),
    []
  )
}

// ─── Compliance Training ─────────────────────────────────────────

export function useTrainingModules(regulation?: string) {
  return useApiCall<TrainingModuleRecord[]>(
    () => complianceTrainingApi.listModules(regulation ? { regulation } : undefined)
      .then(res => ({ data: res.data || [] })),
    [regulation]
  )
}

export function useTrainingLeaderboard() {
  return useApiCall<DeveloperTrainingProfile[]>(
    () => complianceTrainingApi.getLeaderboard()
      .then(res => ({ data: res.data || [] })),
    []
  )
}

// ─── AI Observatory ─────────────────────────────────────────

export function useAIModels(riskLevel?: string) {
  return useApiCall<AIModelRecord[]>(
    () => aiObservatoryApi.listModels(riskLevel ? { risk_level: riskLevel } : undefined)
      .then(res => ({ data: res.data || [] })),
    [riskLevel]
  )
}

export function useAIObservatoryDashboard() {
  return useApiCall<AIObservatoryDashboard>(
    () => aiObservatoryApi.getDashboard(),
    []
  )
}

// ─── Regulation Test Generator ─────────────────────────────────────────

export function useRegTestSuites(regulation?: string) {
  return useApiCall<RegTestSuite[]>(
    () => regulationTestGenApi.listSuites(regulation ? { regulation } : undefined)
      .then(res => ({ data: res.data || [] })),
    [regulation]
  )
}

export function useRegulationCoverages() {
  return useApiCall<RegulationCoverageRecord[]>(
    () => regulationTestGenApi.listCoverages()
      .then(res => ({ data: res.data || [] })),
    []
  )
}

// ─── Sentiment Analyzer ─────────────────────────────────────────

export function useRegulatoryHeatmap() {
  return useApiCall<RiskHeatmapCellRecord[]>(
    () => sentimentAnalyzerApi.getHeatmap()
      .then(res => ({ data: res.data || [] })),
    []
  )
}

export function useCompliancePrioritization() {
  return useApiCall<PrioritizationRecord[]>(
    () => sentimentAnalyzerApi.getPrioritization()
      .then(res => ({ data: res.data || [] })),
    []
  )
}

// ─── Incident Playbook ─────────────────────────────────────────

export function usePlaybooks() {
  return useApiCall<PlaybookRecord[]>(
    () => incidentPlaybookApi.listPlaybooks()
      .then(res => ({ data: res.data || [] })),
    []
  )
}

export function useIncidents(status?: string) {
  return useApiCall<IncidentRecord[]>(
    () => incidentPlaybookApi.listIncidents(status ? { status } : undefined)
      .then(res => ({ data: res.data || [] })),
    [status]
  )
}

// ─── Cost Attribution ─────────────────────────────────────────

export function useCostDashboard() {
  return useApiCall<CostDashboardRecord>(
    () => costAttributionApi.getDashboard(),
    []
  )
}

export function useCostSummaries() {
  return useApiCall<Record<string, unknown>[]>(
    () => costAttributionApi.listSummaries()
      .then(res => ({ data: res.data || [] })),
    []
  )
}

// ─── Blockchain Audit ─────────────────────────────────────────

export function useBlockchainState() {
  return useApiCall<BlockchainStateRecord>(
    () => blockchainAuditApi.getState(),
    []
  )
}

export function useBlockchainVerification() {
  return useApiCall<VerificationResultRecord>(
    () => blockchainAuditApi.verifyChain(),
    []
  )
}

// ─── v2 Feature Hooks ────────────────────────────────────────

import {
  marketplaceV2Api,
  digitalTwinV2Api,
  remediationV2Api,
  multiLlmV2Api,
  evidenceVaultV2Api,
  selfHostedV2Api,
  industryPacksV2Api,
  predictionsV2Api,
  federatedIntelV2Api,
} from '@/lib/api'

// Marketplace v2
export function useAppManifest() {
  return useApiCall<Record<string, unknown>>(() => marketplaceV2Api.getAppManifest(), [])
}

// Digital Twin v2 - Live Tracking
export function useTwinEvents(eventType?: string) {
  return useApiCall<Record<string, unknown>[]>(
    () => digitalTwinV2Api.listEvents({ event_type: eventType }),
    [eventType]
  )
}

export function usePostureTimeline(days = 30) {
  return useApiCall<Record<string, unknown>>(
    () => digitalTwinV2Api.getTimeline(days),
    [days]
  )
}

// Remediation v2 - Fix Templates
export function useFixTemplates(framework?: string) {
  return useApiCall<Record<string, unknown>[]>(
    () => remediationV2Api.listTemplates(framework),
    [framework]
  )
}

// Multi-LLM v2 - Smart Routing
export function useComplexityClassification(text: string) {
  return useApiCall<Record<string, unknown>>(
    () => multiLlmV2Api.classifyComplexity(text),
    [text]
  )
}

// Evidence Vault v2 - Controls
export function useFrameworkControls(framework: string) {
  return useApiCall<Record<string, unknown>[]>(
    () => evidenceVaultV2Api.listControls(framework),
    [framework]
  )
}

// Self-Hosted v2 - Bundles
export function useRegulationBundles() {
  return useApiCall<Record<string, unknown>[]>(
    () => selfHostedV2Api.listBundles(),
    []
  )
}

// Industry Packs v2 - Starter Packs
export function useStarterPacks() {
  return useApiCall<Record<string, unknown>[]>(
    () => industryPacksV2Api.listStarterPacks(),
    []
  )
}

// Predictions v2 - ML Predictions
export function useMlPredictions(params?: { jurisdiction?: string; min_confidence?: number }) {
  return useApiCall<Record<string, unknown>[]>(
    () => predictionsV2Api.listPredictions(params),
    [params?.jurisdiction, params?.min_confidence]
  )
}

export function usePredictionAccuracy() {
  return useApiCall<Record<string, unknown>>(
    () => predictionsV2Api.getAccuracy(),
    []
  )
}

// Federated Intel v2 - Privacy
export function usePrivacyBudget() {
  return useApiCall<Record<string, unknown>>(
    () => federatedIntelV2Api.getPrivacyBudget(),
    []
  )
}

// ═══════════════════════════════════════════════════════════════
// Next-Gen v4 Feature Hooks (39 dashboard wiring)
// ═══════════════════════════════════════════════════════════════

import {
  apiGatewayApi,
  apiMonetizationApi,
  agentSwarmApi,
  agentsMarketplaceApi,
  archAdvisorApi,
  auditWorkspaceApi,
  autoHealingApi,
  autonomousOsApi,
  autoRemediationApi,
  boardReportsApi,
  certAutopilotApi,
  certPipelineApi,
  chaosEngineeringApi,
  cicdRuntimeApi,
  clientSdkApi,
  codeReviewAgentApi,
  complianceApiStandardApi,
  complianceCloningApi,
  complianceDataLakeApi,
  complianceDebtApi,
  complianceEditorApi,
  complianceExportApi,
  complianceObservabilityApi,
  complianceSdkPackagesApi,
  costEngineApi,
  crossCloudMeshApi,
  crossOrgBenchmarkApi,
  crossRepoGraphApi,
  dataMeshFederationApi,
  entityRollupApi,
  gameEngineApi,
  horizonScannerApi,
  policyMarketplaceApi,
  regulationDiffApi,
  complianceCopilotApi,
  iacPolicyApi,
  knowledgeGraphApi,
  pairProgrammingApi,
} from '@/lib/api'

import type {
  GatewayClient,
  GatewayStats,
  MonetizationApi,
  MonetizationRevenue,
  SwarmSession,
  SwarmStats,
  MarketplaceAgent,
  AgentsMarketplaceStats,
  ArchAdvisorStatsRecord,
  AuditWorkspaceItem,
  AutoHealingRun,
  AutoHealingMetrics,
  AutonomousOSEvent,
  AutonomousOSStats,
  AutoRemediationPipeline,
  AutoRemediationStats,
  BoardExecutiveSummary,
  CertJourney,
  CertRun,
  CertPipelineStats,
  ChaosExperiment,
  ChaosStats,
  CICDCheck,
  CICDStats,
  ComplianceApiStandardStatsRecord,
  ApiSpecVersionRecord,
  ReferenceRepoRecord,
  DataLakeStatsRecord,
  ComplianceDebtItemRecord,
  ComplianceDebtStatsRecord,
  EditorStatsRecord,
  ExportJobRecord,
  ExportSummaryRecord,
  ObservabilityMetricRecord,
  ObservabilityPipelineStatsRecord,
  ComplianceSdkPackageRecord,
  ComplianceSdkUsageRecord,
  CostAttributionListRecord,
  CloudAccountRecord,
  CloudPostureRecord,
  OrgBenchmarkStatsRecord,
  CrossRepoGraphRecord,
  DataMeshNodeRecord,
  FederationStatsRecord,
  EntityHierarchyRecord,
  GameScenarioRecord,
  GameLeaderboardRecord,
  HorizonTimelineRecord,
  PolicyPackRecord,
  PolicyMarketplaceStatsRecord,
  RegulationVersionRecord,
  RegulationDiffSummaryRecord,
  CopilotViolationRecord,
  IaCPolicyRuleRecord,
  ImpactScenarioRecord,
  PairRegulationContextRecord,
} from '@/types/nextgen'

// ─── API Gateway ────────────────────────────────────────────────
export function useGatewayClients() {
  return useApiCall<GatewayClient[]>(
    () => apiGatewayApi.listClients().then(res => ({ data: res.data || [] })),
    []
  )
}
export function useGatewayStats() {
  return useApiCall<GatewayStats>(
    () => apiGatewayApi.getStats(),
    []
  )
}

// ─── API Monetization ────────────────────────────────────────────────
export function useMonetizationApis() {
  return useApiCall<MonetizationApi[]>(
    () => apiMonetizationApi.listApis().then(res => ({ data: res.data || [] })),
    []
  )
}
export function useMonetizationRevenue() {
  return useApiCall<MonetizationRevenue>(
    () => apiMonetizationApi.getRevenue(),
    []
  )
}

// ─── Agent Swarm ────────────────────────────────────────────────
export function useSwarmSessions() {
  return useApiCall<SwarmSession[]>(
    () => agentSwarmApi.listSessions().then(res => ({ data: res.data || [] })),
    []
  )
}
export function useSwarmStats() {
  return useApiCall<SwarmStats>(
    () => agentSwarmApi.getStats(),
    []
  )
}

// ─── Agents Marketplace ────────────────────────────────────────────────
export function useMarketplaceAgents(query?: string) {
  return useApiCall<MarketplaceAgent[]>(
    () => agentsMarketplaceApi.searchAgents(query ? { query } : undefined)
      .then(res => ({ data: res.data || [] })),
    [query]
  )
}
export function useAgentsMarketplaceStats() {
  return useApiCall<AgentsMarketplaceStats>(
    () => agentsMarketplaceApi.getStats(),
    []
  )
}

// ─── Arch Advisor ────────────────────────────────────────────────
export function useArchAdvisorStats() {
  return useApiCall<ArchAdvisorStatsRecord>(
    () => archAdvisorApi.getStats(),
    []
  )
}
export function useArchAdvisorFrameworks() {
  return useApiCall<string[]>(
    () => archAdvisorApi.listFrameworks().then(res => ({ data: res.data || [] })),
    []
  )
}

// ─── Audit Workspace ────────────────────────────────────────────────
export function useAuditWorkspaces(org_id?: string) {
  return useApiCall<AuditWorkspaceItem[]>(
    () => auditWorkspaceApi.listWorkspaces(org_id).then(res => ({ data: res.data || [] })),
    [org_id]
  )
}

// ─── Auto Healing ────────────────────────────────────────────────
export function useAutoHealingRuns(state?: string) {
  return useApiCall<AutoHealingRun[]>(
    () => autoHealingApi.listRuns(state).then(res => ({ data: (res.data as { runs?: AutoHealingRun[] })?.runs || res.data || [] })),
    [state]
  )
}
export function useAutoHealingMetrics() {
  return useApiCall<AutoHealingMetrics>(
    () => autoHealingApi.getMetrics(),
    []
  )
}

// ─── Autonomous OS ────────────────────────────────────────────────
export function useAutonomousOSEvents() {
  return useApiCall<AutonomousOSEvent[]>(
    () => autonomousOsApi.listEvents().then(res => ({ data: res.data || [] })),
    []
  )
}
export function useAutonomousOSStats() {
  return useApiCall<AutonomousOSStats>(
    () => autonomousOsApi.getStats(),
    []
  )
}

// ─── Auto Remediation ────────────────────────────────────────────────
export function useAutoRemediationPipelines(status?: string) {
  return useApiCall<AutoRemediationPipeline[]>(
    () => autoRemediationApi.listPipelines(status ? { pipeline_status: status } : undefined)
      .then(res => ({ data: res.data || [] })),
    [status]
  )
}
export function useAutoRemediationStats() {
  return useApiCall<AutoRemediationStats>(
    () => autoRemediationApi.getStats(),
    []
  )
}

// ─── Board Reports ────────────────────────────────────────────────
export function useBoardExecutiveSummary(org_id?: string, period?: string) {
  return useApiCall<BoardExecutiveSummary>(
    () => boardReportsApi.getExecutiveSummary({ org_id, period }),
    [org_id, period]
  )
}

// ─── Cert Autopilot ────────────────────────────────────────────────
export function useCertJourneys() {
  return useApiCall<CertJourney[]>(
    () => certAutopilotApi.listJourneys().then(res => ({ data: (res.data as { journeys?: CertJourney[] })?.journeys || res.data || [] })),
    []
  )
}

// ─── Cert Pipeline ────────────────────────────────────────────────
export function useCertRuns(params?: { framework?: string; repo?: string }) {
  return useApiCall<CertRun[]>(
    () => certPipelineApi.listRuns(params).then(res => ({ data: res.data || [] })),
    [params?.framework, params?.repo]
  )
}
export function useCertPipelineStats() {
  return useApiCall<CertPipelineStats>(
    () => certPipelineApi.getStats(),
    []
  )
}

// ─── Chaos Engineering ────────────────────────────────────────────────
export function useChaosExperiments(status?: string) {
  return useApiCall<ChaosExperiment[]>(
    () => chaosEngineeringApi.listExperiments(status).then(res => ({ data: res.data || [] })),
    [status]
  )
}
export function useChaosStats() {
  return useApiCall<ChaosStats>(
    () => chaosEngineeringApi.getStats(),
    []
  )
}

// ─── CICD Runtime ────────────────────────────────────────────────
export function useCICDChecks() {
  return useApiCall<CICDCheck[]>(
    () => cicdRuntimeApi.listChecks().then(res => ({ data: res.data || [] })),
    []
  )
}
export function useCICDStats() {
  return useApiCall<CICDStats>(
    () => cicdRuntimeApi.getStats(),
    []
  )
}

// ─── Client SDK ────────────────────────────────────────────────
export function useClientSDKPackages() {
  return useApiCall<Record<string, unknown>[]>(
    () => clientSdkApi.listPackages().then(res => ({ data: res.data || [] })),
    []
  )
}
export function useClientSDKStats() {
  return useApiCall<Record<string, unknown>>(
    () => clientSdkApi.getStats(),
    []
  )
}

// ─── Code Review Agent ────────────────────────────────────────────────
export function useCodeReviews(repo?: string) {
  return useApiCall<Record<string, unknown>[]>(
    () => codeReviewAgentApi.listReviews(repo ? { repo } : undefined)
      .then(res => ({ data: res.data || [] })),
    [repo]
  )
}
export function useCodeReviewStats() {
  return useApiCall<Record<string, unknown>>(
    () => codeReviewAgentApi.getStats(),
    []
  )
}

// ─── Compliance API Standard ────────────────────────────────────────────────
export function useApiSpecVersions() {
  return useApiCall<ApiSpecVersionRecord[]>(
    () => complianceApiStandardApi.listVersions().then(res => ({ data: res.data || [] })),
    []
  )
}
export function useComplianceApiStandardStats() {
  return useApiCall<ComplianceApiStandardStatsRecord>(
    () => complianceApiStandardApi.getStats(),
    []
  )
}

// ─── Compliance Cloning ────────────────────────────────────────────────
export function useReferenceRepos(industry?: string) {
  return useApiCall<ReferenceRepoRecord[]>(
    () => complianceCloningApi.listReferenceRepos(industry ? { industry } : undefined)
      .then(res => ({ data: res.data || [] })),
    [industry]
  )
}

// ─── Compliance Data Lake ────────────────────────────────────────────────
export function useDataLakeStats() {
  return useApiCall<DataLakeStatsRecord>(
    () => complianceDataLakeApi.getStats(),
    []
  )
}

// ─── Compliance Debt ────────────────────────────────────────────────
export function useComplianceDebtItems(framework?: string) {
  return useApiCall<ComplianceDebtItemRecord[]>(
    () => complianceDebtApi.listItems(framework).then(res => ({ data: res.data || [] })),
    [framework]
  )
}
export function useComplianceDebtStats() {
  return useApiCall<ComplianceDebtStatsRecord>(
    () => complianceDebtApi.getStats(),
    []
  )
}

// ─── Compliance Editor ────────────────────────────────────────────────
export function useComplianceEditorStats() {
  return useApiCall<EditorStatsRecord>(
    () => complianceEditorApi.getStats(),
    []
  )
}

// ─── Compliance Export ────────────────────────────────────────────────
export function useExportJobs(limit?: number) {
  return useApiCall<ExportJobRecord[]>(
    () => complianceExportApi.listExports(limit).then(res => ({ data: res.data || [] })),
    [limit]
  )
}
export function useExportSummary() {
  return useApiCall<ExportSummaryRecord>(
    () => complianceExportApi.getSummary(),
    []
  )
}

// ─── Compliance Observability ────────────────────────────────────────────────
export function useObservabilityMetrics() {
  return useApiCall<ObservabilityMetricRecord[]>(
    () => complianceObservabilityApi.listMetrics().then(res => ({ data: res.data || [] })),
    []
  )
}
export function useObservabilityStats() {
  return useApiCall<ObservabilityPipelineStatsRecord>(
    () => complianceObservabilityApi.getStats(),
    []
  )
}

// ─── Compliance SDK ────────────────────────────────────────────────
export function useComplianceSdkPackages(language?: string) {
  return useApiCall<ComplianceSdkPackageRecord[]>(
    () => complianceSdkPackagesApi.listSdks(language).then(res => ({ data: res.data || [] })),
    [language]
  )
}
export function useComplianceSdkUsage() {
  return useApiCall<ComplianceSdkUsageRecord>(
    () => complianceSdkPackagesApi.getUsage(),
    []
  )
}

// ─── Cost Engine ────────────────────────────────────────────────
export function useCostAttributionList() {
  return useApiCall<CostAttributionListRecord>(
    () => costEngineApi.listAttributions(),
    []
  )
}
export function useCostEngineRoi() {
  return useApiCall<Record<string, unknown>>(
    () => costEngineApi.getRoi(),
    []
  )
}

// ─── Cross Cloud Mesh ────────────────────────────────────────────────
export function useCloudAccounts() {
  return useApiCall<CloudAccountRecord[]>(
    () => crossCloudMeshApi.listAccounts().then(res => ({ data: res.data || [] })),
    []
  )
}
export function useCloudPosture() {
  return useApiCall<CloudPostureRecord>(
    () => crossCloudMeshApi.getPosture(),
    []
  )
}

// ─── Cross Org Benchmark ────────────────────────────────────────────────
export function useCrossOrgBenchmarkStats() {
  return useApiCall<OrgBenchmarkStatsRecord>(
    () => crossOrgBenchmarkApi.getStats(),
    []
  )
}

// ─── Cross Repo Graph ────────────────────────────────────────────────
export function useCrossRepoGraph() {
  return useApiCall<CrossRepoGraphRecord>(
    () => crossRepoGraphApi.getGraph(),
    []
  )
}

// ─── Data Mesh Federation ────────────────────────────────────────────────
export function useDataMeshNodes() {
  return useApiCall<DataMeshNodeRecord[]>(
    () => dataMeshFederationApi.listNodes().then(res => ({ data: res.data || [] })),
    []
  )
}
export function useFederationStats() {
  return useApiCall<FederationStatsRecord>(
    () => dataMeshFederationApi.getStats(),
    []
  )
}

// ─── Entity Rollup ────────────────────────────────────────────────
export function useEntityHierarchy() {
  return useApiCall<EntityHierarchyRecord[]>(
    () => entityRollupApi.getHierarchy().then(res => ({ data: res.data || [] })),
    []
  )
}

// ─── Game Engine ────────────────────────────────────────────────
export function useGameScenarios(category?: string) {
  return useApiCall<GameScenarioRecord[]>(
    () => gameEngineApi.listScenarios(category ? { category } : undefined)
      .then(res => ({ data: res.data || [] })),
    [category]
  )
}
export function useGameLeaderboard(limit?: number) {
  return useApiCall<GameLeaderboardRecord[]>(
    () => gameEngineApi.getLeaderboard(limit).then(res => ({ data: res.data || [] })),
    [limit]
  )
}

// ─── Horizon Scanner ────────────────────────────────────────────────
export function useHorizonTimeline(params?: { jurisdiction?: string; framework?: string }) {
  return useApiCall<HorizonTimelineRecord>(
    () => horizonScannerApi.getTimeline(params),
    [params?.jurisdiction, params?.framework]
  )
}

// ─── Policy Marketplace ────────────────────────────────────────────────
export function usePolicyPacks() {
  return useApiCall<PolicyPackRecord[]>(
    () => policyMarketplaceApi.listPacks().then(res => ({ data: (res.data as { packs?: PolicyPackRecord[] })?.packs || res.data || [] })),
    []
  )
}
export function usePolicyMarketplaceStats() {
  return useApiCall<PolicyMarketplaceStatsRecord>(
    () => policyMarketplaceApi.getStats(),
    []
  )
}

// ─── Regulation Diff ────────────────────────────────────────────────
export function useRegulationVersions(regulation?: string) {
  return useApiCall<RegulationVersionRecord[]>(
    () => regulationDiffApi.listVersions(regulation).then(res => ({ data: res.data || [] })),
    [regulation]
  )
}
export function useRegulationDiffs(regulation?: string) {
  return useApiCall<RegulationDiffSummaryRecord[]>(
    () => regulationDiffApi.listDiffs(regulation).then(res => ({ data: res.data || [] })),
    [regulation]
  )
}

// ─── Compliance Copilot ────────────────────────────────────────────────
export function useComplianceCopilotViolations(framework?: string) {
  return useApiCall<CopilotViolationRecord[]>(
    () => complianceCopilotApi.listViolations(framework ? { framework } : undefined)
      .then(res => ({ data: res.data || [] })),
    [framework]
  )
}

// ─── IaC Policy Engine ────────────────────────────────────────────────
export function useIaCRules(provider?: string) {
  return useApiCall<IaCPolicyRuleRecord[]>(
    () => iacPolicyApi.listRules(provider ? { provider } : undefined)
      .then(res => ({ data: (res.data as { rules?: IaCPolicyRuleRecord[] })?.rules || res.data || [] })),
    [provider]
  )
}

// ─── Knowledge Graph ────────────────────────────────────────────────
export function useKnowledgeGraphNodeTypes() {
  return useApiCall<Record<string, unknown>>(
    () => knowledgeGraphApi.getNodeTypes(),
    []
  )
}

// ─── Pair Programming ────────────────────────────────────────────────
export function usePairProgrammingContext(language: string) {
  return useApiCall<PairRegulationContextRecord[]>(
    () => pairProgrammingApi.getContext(language).then(res => ({ data: res.data || [] })),
    [language]
  )
}

// ─── Impact Simulator ────────────────────────────────────────────────
export function useImpactScenarios() {
  return useApiCall<ImpactScenarioRecord[]>(
    () => impactSimulatorApi.listScenarios().then(res => ({ data: res.data || [] })),
    []
  )
}
