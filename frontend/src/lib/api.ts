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
