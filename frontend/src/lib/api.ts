import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          })
          localStorage.setItem('access_token', response.data.access_token)
          localStorage.setItem('refresh_token', response.data.refresh_token)
          // Retry original request
          error.config.headers.Authorization = `Bearer ${response.data.access_token}`
          return api(error.config)
        } catch {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      } else {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, password: string, fullName: string) =>
    api.post('/auth/register', { email, password, full_name: fullName }),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
}

// Organizations API
export const organizationsApi = {
  list: () => api.get('/organizations'),
  get: (id: string) => api.get(`/organizations/${id}`),
  create: (data: { name: string; slug: string }) => api.post('/organizations', data),
  update: (id: string, data: Record<string, unknown>) => api.patch(`/organizations/${id}`, data),
}

// Regulations API
export const regulationsApi = {
  list: (params?: { jurisdiction?: string; framework?: string }) =>
    api.get('/regulations', { params }),
  get: (id: string) => api.get(`/regulations/${id}`),
  getRequirements: (id: string) => api.get(`/regulations/${id}/requirements`),
}

// Requirements API
export const requirementsApi = {
  list: (params?: { regulation_id?: string; category?: string }) =>
    api.get('/requirements', { params }),
  get: (id: string) => api.get(`/requirements/${id}`),
  review: (id: string, approved: boolean) =>
    api.post(`/requirements/${id}/review`, { approved }),
}

// Customer Profiles API
export const customerProfilesApi = {
  list: () => api.get('/customer-profiles'),
  get: (id: string) => api.get(`/customer-profiles/${id}`),
  create: (data: Record<string, unknown>) => api.post('/customer-profiles', data),
  update: (id: string, data: Record<string, unknown>) => api.patch(`/customer-profiles/${id}`, data),
}

// Repositories API
export const repositoriesApi = {
  list: (profileId?: string) =>
    api.get('/repositories', { params: profileId ? { profile_id: profileId } : {} }),
  get: (id: string) => api.get(`/repositories/${id}`),
  create: (data: Record<string, unknown>) => api.post('/repositories', data),
  delete: (id: string) => api.delete(`/repositories/${id}`),
  analyze: (id: string) => api.post(`/repositories/${id}/analyze`),
}

// Codebase Mappings API
export const mappingsApi = {
  list: (params?: { repository_id?: string; requirement_id?: string }) =>
    api.get('/mappings', { params }),
  get: (id: string) => api.get(`/mappings/${id}`),
  review: (id: string, status: string, notes?: string) =>
    api.post(`/mappings/${id}/review`, { compliance_status: status, notes }),
}

// Compliance API
export const complianceApi = {
  getStatus: (repositoryId?: string) =>
    api.get('/compliance/status', { params: repositoryId ? { repository_id: repositoryId } : {} }),
  assessImpact: (mappingId: string) =>
    api.post(`/compliance/assess/${mappingId}`),
  generateCode: (mappingId: string, options?: { include_tests?: boolean }) =>
    api.post('/compliance/generate', { mapping_id: mappingId, ...options }),
}

// Audit API
export const auditApi = {
  listTrail: (params?: { regulation_id?: string; event_type?: string }) =>
    api.get('/audit/trail', { params }),
  listActions: (params?: { status?: string; repository_id?: string }) =>
    api.get('/audit/actions', { params }),
  getAction: (id: string) => api.get(`/audit/actions/${id}`),
  updateAction: (id: string, data: Record<string, unknown>) => api.patch(`/audit/actions/${id}`, data),
}

// --- Next-Gen Feature APIs ---

// Compliance Testing Suite API
export const testingApi = {
  generateSuite: (data: { regulation: string; framework?: string; target_files?: string[]; pattern_ids?: string[] }) =>
    api.post('/testing/generate', data),
  listPatterns: (params?: { regulation?: string; category?: string }) =>
    api.get('/testing/patterns', { params }),
  detectFrameworks: (data: { repo: string; files?: string[] }) =>
    api.post('/testing/detect-frameworks', data),
  validateTests: (suiteId: string) =>
    api.post(`/testing/validate/${suiteId}`),
}

// Architecture Advisor API
export const architectureAdvisorApi = {
  analyze: (data: { repo: string; files?: string[]; regulations?: string[] }) =>
    api.post('/architecture-advisor/analyze', data),
  listPatterns: () =>
    api.get('/architecture-advisor/patterns'),
  getScore: (repo: string) =>
    api.get(`/architecture-advisor/score/${repo}`),
}

// Drift Detection API
export const driftDetectionApi = {
  captureBaseline: (data: { repo: string; branch?: string }) =>
    api.post('/drift-detection/baseline', data),
  detectDrift: (repo: string, params?: { current_score?: number }) =>
    api.get(`/drift-detection/drift/${repo}`, { params }),
  getReport: (repo: string) =>
    api.get(`/drift-detection/report/${repo}`),
  getAlerts: () =>
    api.get('/drift-detection/alerts'),
}

// Cost Calculator API
export const costCalculatorApi = {
  predict: (data: { regulation: string; complexity?: string; team_size?: number }) =>
    api.post('/cost-calculator/predict', data),
  compareScenarios: (data: { regulation: string; scenarios: string[] }) =>
    api.post('/cost-calculator/compare', data),
  calculateROI: (data: { regulation: string }) =>
    api.post('/cost-calculator/roi', data),
  getHistory: () =>
    api.get('/cost-calculator/history'),
}

// Evidence Vault API
export const evidenceVaultApi = {
  storeEvidence: (data: Record<string, unknown>) =>
    api.post('/evidence-vault/evidence', data),
  getEvidence: (params?: { framework?: string }) =>
    api.get('/evidence-vault/evidence', { params }),
  verifyChain: (framework: string) =>
    api.get(`/evidence-vault/verify/${framework}`),
  getControlMappings: (framework: string) =>
    api.get(`/evidence-vault/controls/${framework}`),
  createAuditorSession: (data: { auditor_email: string; auditor_name: string }) =>
    api.post('/evidence-vault/auditor-sessions', data),
  generateReport: (framework: string) =>
    api.get(`/evidence-vault/report/${framework}`),
}

// Federated Intelligence API
export const federatedIntelApi = {
  getNetworkStats: () =>
    api.get('/federated-intel/network'),
  getThreats: (params?: { category?: string }) =>
    api.get('/federated-intel/threats', { params }),
  getPatterns: () =>
    api.get('/federated-intel/patterns'),
  getBenchmarks: () =>
    api.get('/federated-intel/benchmarks'),
  getThreatFeed: () =>
    api.get('/federated-intel/feed'),
}

// Marketplace App API
export const marketplaceAppApi = {
  getListingInfo: () =>
    api.get('/marketplace-app/listing'),
  getInstallations: () =>
    api.get('/marketplace-app/installations'),
  handleInstallation: (data: Record<string, unknown>) =>
    api.post('/marketplace-app/install', data),
}

// Industry Packs API
export const industryPacksApi = {
  listPacks: () =>
    api.get('/industry-packs'),
  getPack: (vertical: string) =>
    api.get(`/industry-packs/${vertical}`),
  provisionPack: (vertical: string) =>
    api.post(`/industry-packs/${vertical}/provision`),
}

// Natural Language Query API
export const nlQueryApi = {
  query: (data: { query: string; context?: Record<string, unknown> }) =>
    api.post('/nl-query/query', data),
  getHistory: (limit = 20) =>
    api.get('/nl-query/history', { params: { limit } }),
  submitFeedback: (data: { query_id: string; helpful: boolean }) =>
    api.post('/nl-query/feedback', data),
  getIntents: () =>
    api.get('/nl-query/intents'),
}

// Multi-LLM API
export const multiLlmApi = {
  parse: (data: { text: string; framework?: string; strategy?: string }) =>
    api.post('/multi-llm/parse', data),
  getProviders: () =>
    api.get('/multi-llm/providers'),
  addProvider: (data: { provider: string; model_name: string; weight?: number }) =>
    api.post('/multi-llm/providers', data),
  removeProvider: (provider: string) =>
    api.delete(`/multi-llm/providers/${provider}`),
  getConfig: () =>
    api.get('/multi-llm/config'),
}

// Impact Timeline API
export const impactTimelineApi = {
  getTimeline: (params?: { framework?: string; jurisdiction?: string; days_ahead?: number }) =>
    api.get('/impact-timeline/timeline', { params }),
  addEvent: (data: Record<string, unknown>) =>
    api.post('/impact-timeline/events', data),
  generateTasks: (eventId: string) =>
    api.post(`/impact-timeline/events/${eventId}/tasks`),
  getTasks: (params?: { task_status?: string }) =>
    api.get('/impact-timeline/tasks', { params }),
}

// Audit Autopilot API
export const auditAutopilotApi = {
  runGapAnalysis: (framework: string) =>
    api.post(`/audit-autopilot/gap-analysis/${framework}`),
  generateEvidencePackage: (framework: string) =>
    api.post(`/audit-autopilot/evidence-package/${framework}`),
  generateReadinessReport: (framework: string) =>
    api.post(`/audit-autopilot/readiness-report/${framework}`),
  listFrameworks: () =>
    api.get('/audit-autopilot/frameworks'),
}

// Policy SDK API
export const policySdkApi = {
  listPolicies: (params?: { category?: string; framework?: string }) =>
    api.get('/policy-sdk/policies', { params }),
  createPolicy: (data: Record<string, unknown>) =>
    api.post('/policy-sdk/policies', data),
  validatePolicy: (policyId: string) =>
    api.post(`/policy-sdk/policies/${policyId}/validate`),
  publishPolicy: (policyId: string, publisher: string) =>
    api.post(`/policy-sdk/policies/${policyId}/publish`, { publisher }),
  searchMarketplace: (params?: { query?: string; category?: string; framework?: string }) =>
    api.get('/policy-sdk/marketplace', { params }),
  listSDKs: () =>
    api.get('/policy-sdk/sdks'),
}

// Compliance Sandbox API
export const complianceSandboxApi = {
  listScenarios: () =>
    api.get('/compliance-sandbox/scenarios'),
  getScenario: (id: string) =>
    api.get(`/compliance-sandbox/scenarios/${id}`),
  createEnvironment: (scenarioId: string) =>
    api.post(`/compliance-sandbox/scenarios/${scenarioId}/start`),
  getEnvironment: (envId: string) =>
    api.get(`/compliance-sandbox/environments/${envId}`),
}

// IDE Agent / Copilot API
export const ideAgentApi = {
  ragSearch: (data: { query: string; regulations?: string[]; top_k?: number }) =>
    api.post('/ide-agent/rag-search', data),
  submitFeedback: (data: { session_id?: string; violation_id?: string; fix_id?: string; rating: string; comment?: string; was_applied?: boolean }) =>
    api.post('/ide-agent/feedback', data),
  getFeedbackStats: () =>
    api.get('/ide-agent/feedback/stats'),
}

// Impact Simulator API
export const impactSimulatorApi = {
  runSimulation: (data: { regulation: string; scenario_type?: string }) =>
    api.post('/impact-simulator/simulate', data),
  listScenarios: () =>
    api.get('/impact-simulator/scenarios'),
  getBlastRadius: (scenarioId: string) =>
    api.get(`/impact-simulator/blast-radius/${scenarioId}`),
  compareScenarios: (data: { scenario_ids: string[] }) =>
    api.post('/impact-simulator/compare-detailed', data),
}

// Remediation Workflow API
export const remediationApi = {
  listWorkflows: (params?: { status?: string }) =>
    api.get('/remediation/workflows', { params }),
  createWorkflow: (data: { violation_id: string; description?: string }) =>
    api.post('/remediation/workflows', data),
  getAnalytics: () =>
    api.get('/remediation/analytics'),
  createApprovalChain: (workflowId: string) =>
    api.post(`/remediation/workflows/${workflowId}/approval-chain`),
  processApproval: (workflowId: string, data: { step_id: string; approved: boolean; comment?: string }) =>
    api.post(`/remediation/workflows/${workflowId}/process-approval`, data),
  rollbackWorkflow: (workflowId: string, data: { reason: string; rolled_back_by?: string }) =>
    api.post(`/remediation/workflows/${workflowId}/rollback-with-record`, data),
  getRollbackHistory: (params?: { workflow_id?: string }) =>
    api.get('/remediation/rollback-history', { params }),
}

// Posture Scoring API
export const postureScoringApi = {
  getDynamicScore: (repo?: string) =>
    api.get('/posture/dynamic-score', { params: repo ? { repo } : {} }),
  getBenchmark: (industry: string, repo?: string) =>
    api.get(`/posture/dynamic-benchmark/${industry}`, { params: repo ? { repo } : {} }),
  getHistory: (repo?: string) =>
    api.get('/posture/dynamic-history', { params: repo ? { repo } : {} }),
}

// Enhanced Drift Detection API
export const driftDetectionEnhancedApi = {
  getTrend: (repo: string, period?: string) =>
    api.get(`/drift-detection/trend/${repo}`, { params: period ? { period } : {} }),
  getTopDrifting: (repo: string, limit?: number) =>
    api.get(`/drift-detection/top-drifting/${repo}`, { params: limit ? { limit } : {} }),
}

// Enhanced Marketplace API
export const marketplaceEnhancedApi = {
  getUsageSummary: (installationId: string) =>
    api.get(`/marketplace-app/installations/${installationId}/usage`),
  checkPlanEnforcement: (installationId: string, action?: string) =>
    api.get(`/marketplace-app/installations/${installationId}/plan-check`, { params: action ? { action } : {} }),
}

// Enhanced Evidence Vault API
export const evidenceVaultEnhancedApi = {
  getCoverage: (framework: string) =>
    api.get(`/evidence-vault/coverage/${framework}`),
  verifyChainEnhanced: (framework: string) =>
    api.get(`/evidence-vault/verify-enhanced/${framework}`),
  getGaps: (framework: string) =>
    api.get(`/evidence-vault/gaps/${framework}`),
}

// Enhanced Multi-LLM API
export const multiLlmEnhancedApi = {
  analyzeDivergence: (consensusId: string) =>
    api.get(`/multi-llm/divergence/${consensusId}`),
  getProviderHealth: () =>
    api.get('/multi-llm/provider-health'),
}

// Enhanced Self-Hosted API
export const selfHostedEnhancedApi = {
  validateLicenseCrypto: (data: { license_key: string }) =>
    api.post('/self-hosted/validate-license', data),
  listOfflineBundles: () =>
    api.get('/self-hosted/offline-bundles'),
  installBundle: (bundleId: string) =>
    api.post(`/self-hosted/offline-bundles/${bundleId}/install`),
  getAirGapStatus: () =>
    api.get('/self-hosted/air-gap-status'),
}

// Enhanced Industry Packs API
export const industryPacksEnhancedApi = {
  getWizardSteps: (vertical: string) =>
    api.get(`/industry-packs/${vertical}/wizard`),
  provisionWithWizard: (data: { vertical: string; wizard_answers: Record<string, unknown> }) =>
    api.post('/industry-packs/provision-wizard', data),
}

// ═══════════════════════════════════════════════════════════════
// Next-Gen v3 Feature APIs
// ═══════════════════════════════════════════════════════════════

// Cross-Border Data Transfer API
export const crossBorderTransferApi = {
  discoverFlows: (data: { repo: string; source_jurisdiction?: string }) =>
    api.post('/cross-border-transfer/discover', data),
  listFlows: (params?: { source?: string; destination?: string }) =>
    api.get('/cross-border-transfer/flows', { params }),
  generateSCC: (data: { flow_id: string; exporter?: string; importer?: string }) =>
    api.post('/cross-border-transfer/scc/generate', data),
  listSCCs: () =>
    api.get('/cross-border-transfer/scc'),
  runTIA: (flowId: string) =>
    api.post(`/cross-border-transfer/tia/${flowId}`),
  getAdequacyDecisions: () =>
    api.get('/cross-border-transfer/adequacy'),
  getAlerts: () =>
    api.get('/cross-border-transfer/alerts'),
  getReport: () =>
    api.get('/cross-border-transfer/report'),
  getJurisdictions: () =>
    api.get('/cross-border-transfer/jurisdictions'),
}

// Stress Testing API
export const stressTestingApi = {
  createScenario: (data: { name: string; scenario_type: string; description?: string }) =>
    api.post('/stress-testing/scenarios', data),
  listScenarios: () =>
    api.get('/stress-testing/scenarios'),
  runSimulation: (data: { scenario_id: string; iterations?: number }) =>
    api.post('/stress-testing/simulate', data),
  getSimulation: (runId: string) =>
    api.get(`/stress-testing/simulations/${runId}`),
  getReport: () =>
    api.get('/stress-testing/report'),
}

// Zero-Trust Scanner API
export const zeroTrustScannerApi = {
  scan: (data: { repo: string; scan_type?: string }) =>
    api.post('/zero-trust-scanner/scan', data),
  listPolicies: () =>
    api.get('/zero-trust-scanner/policies'),
  listViolations: (params?: { status?: string; framework?: string }) =>
    api.get('/zero-trust-scanner/violations', { params }),
  remediateViolation: (violationId: string) =>
    api.post(`/zero-trust-scanner/violations/${violationId}/remediate`),
  getSummary: () =>
    api.get('/zero-trust-scanner/summary'),
}

// Compliance Training API
export const complianceTrainingApi = {
  triggerTraining: (data: { developer_id: string; violation_type: string; regulation: string }) =>
    api.post('/compliance-training/trigger', data),
  getProfile: (developerId: string) =>
    api.get(`/compliance-training/profile/${developerId}`),
  listModules: (params?: { regulation?: string; level?: string }) =>
    api.get('/compliance-training/modules', { params }),
  completeAssignment: (assignmentId: string, data: { quiz_score: number }) =>
    api.post(`/compliance-training/assignments/${assignmentId}/complete`, data),
  getTeamReport: (team: string) =>
    api.get(`/compliance-training/team-report/${team}`),
  getLeaderboard: () =>
    api.get('/compliance-training/leaderboard'),
}

// AI Observatory API
export const aiObservatoryApi = {
  registerModel: (data: { name: string; model_type: string; version: string; framework: string; use_case: string }) =>
    api.post('/ai-observatory/models', data),
  listModels: (params?: { risk_level?: string; status?: string }) =>
    api.get('/ai-observatory/models', { params }),
  classifyRisk: (modelId: string) =>
    api.post(`/ai-observatory/models/${modelId}/classify`),
  runBiasAssessment: (modelId: string, data: { protected_attributes?: string[] }) =>
    api.post(`/ai-observatory/models/${modelId}/bias-assessment`, data),
  assessCompliance: (modelId: string) =>
    api.post(`/ai-observatory/models/${modelId}/assess`),
  getDashboard: () =>
    api.get('/ai-observatory/dashboard'),
}

// Regulation Test Generator API
export const regulationTestGenApi = {
  generateSuite: (data: { regulation: string; framework: string; target_files?: string[] }) =>
    api.post('/regulation-test-gen/generate', data),
  listSuites: (params?: { regulation?: string }) =>
    api.get('/regulation-test-gen/suites', { params }),
  getCoverage: (regulation: string) =>
    api.get(`/regulation-test-gen/coverage/${regulation}`),
  runTests: (suiteId: string) =>
    api.post(`/regulation-test-gen/suites/${suiteId}/run`),
  listCoverages: () =>
    api.get('/regulation-test-gen/coverage'),
}

// Sentiment Analyzer API
export const sentimentAnalyzerApi = {
  analyze: (data: { regulation: string; jurisdiction?: string }) =>
    api.post('/sentiment-analyzer/analyze', data),
  listSentiments: (params?: { jurisdiction?: string }) =>
    api.get('/sentiment-analyzer/sentiments', { params }),
  getHeatmap: () =>
    api.get('/sentiment-analyzer/heatmap'),
  getPrioritization: () =>
    api.get('/sentiment-analyzer/prioritization'),
  getReport: () =>
    api.get('/sentiment-analyzer/report'),
}

// Incident Playbook API
export const incidentPlaybookApi = {
  listPlaybooks: (params?: { incident_type?: string }) =>
    api.get('/incident-playbook/playbooks', { params }),
  getPlaybook: (playbookId: string) =>
    api.get(`/incident-playbook/playbooks/${playbookId}`),
  createIncident: (data: { playbook_id: string; severity: string; title: string; description: string; affected_data_subjects?: number; jurisdictions?: string[] }) =>
    api.post('/incident-playbook/incidents', data),
  updateIncidentStatus: (incidentId: string, data: { status: string }) =>
    api.patch(`/incident-playbook/incidents/${incidentId}/status`, data),
  listIncidents: (params?: { status?: string }) =>
    api.get('/incident-playbook/incidents', { params }),
  generateReport: (incidentId: string) =>
    api.post(`/incident-playbook/incidents/${incidentId}/report`),
}

// Cost Attribution API
export const costAttributionApi = {
  recordCost: (data: { regulation: string; category: string; amount: number; description: string; code_module?: string }) =>
    api.post('/cost-attribution/costs', data),
  listCosts: (params?: { regulation?: string; category?: string }) =>
    api.get('/cost-attribution/costs', { params }),
  getRegulationSummary: (regulation: string) =>
    api.get(`/cost-attribution/summary/${regulation}`),
  analyzeROI: (regulation: string) =>
    api.post(`/cost-attribution/roi/${regulation}`),
  getDashboard: () =>
    api.get('/cost-attribution/dashboard'),
  listSummaries: () =>
    api.get('/cost-attribution/summaries'),
}

// Blockchain Audit API
export const blockchainAuditApi = {
  addBlock: (data: { block_type: string; data: Record<string, unknown> }) =>
    api.post('/blockchain-audit/blocks', data),
  getChain: () =>
    api.get('/blockchain-audit/chain'),
  verifyChain: () =>
    api.get('/blockchain-audit/verify'),
  getState: () =>
    api.get('/blockchain-audit/state'),
  createSmartContract: (data: { name: string; contract_type: string; conditions: Record<string, unknown>[]; auto_approve?: boolean }) =>
    api.post('/blockchain-audit/smart-contracts', data),
  listSmartContracts: () =>
    api.get('/blockchain-audit/smart-contracts'),
}
