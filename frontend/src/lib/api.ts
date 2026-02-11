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
