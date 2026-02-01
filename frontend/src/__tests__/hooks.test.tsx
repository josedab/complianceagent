import { renderHook, waitFor, act } from '@testing-library/react'

// Declare mocks inside the factory function to avoid hoisting issues
jest.mock('@/lib/api', () => ({
  complianceApi: {
    getStatus: jest.fn(),
  },
  regulationsApi: {
    list: jest.fn(),
  },
  auditApi: {
    listActions: jest.fn(),
    listTrail: jest.fn(),
    getAction: jest.fn(),
    updateAction: jest.fn(),
  },
  repositoriesApi: {
    list: jest.fn(),
    create: jest.fn(),
    delete: jest.fn(),
  },
  mappingsApi: {
    list: jest.fn().mockResolvedValue({ data: [] }),
  },
  requirementsApi: {
    list: jest.fn().mockResolvedValue({ data: [] }),
  },
}))

// Import after mocking
import { complianceApi, regulationsApi, auditApi, repositoriesApi } from '@/lib/api'
import {
  useDashboardStats,
  useRegulations,
  useRepositories,
  useComplianceActions,
  useAuditTrail,
  useCreateRepository,
} from '@/hooks/useApi'

describe('useApi Hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Set up default successful responses
    ;(complianceApi.getStatus as jest.Mock).mockResolvedValue({
      data: {
        overall_score: 85,
        compliant: 42,
        partial: 8,
        non_compliant: 3,
        pending: 5,
        trend_percentage: 2.3,
      },
    })
    ;(regulationsApi.list as jest.Mock).mockResolvedValue({
      data: {
        items: [
          { id: '1', name: 'GDPR', framework: 'GDPR', short_name: 'GDPR' },
          { id: '2', name: 'CCPA', framework: 'CCPA', short_name: 'CCPA' },
        ],
      },
    })
    ;(auditApi.listActions as jest.Mock).mockResolvedValue({
      data: { items: [] },
    })
    ;(auditApi.listTrail as jest.Mock).mockResolvedValue({
      data: { items: [] },
    })
    ;(repositoriesApi.list as jest.Mock).mockResolvedValue({
      data: [
        { id: '1', platform: 'github', owner: 'acme', name: 'webapp' },
        { id: '2', platform: 'gitlab', owner: 'acme', name: 'api' },
      ],
    })
    ;(repositoriesApi.create as jest.Mock).mockResolvedValue({
      data: { id: 'new-repo-id', platform: 'github', owner: 'acme', name: 'new-repo' },
    })
  })

  describe('useDashboardStats', () => {
    it('fetches and returns dashboard statistics', async () => {
      const { result } = renderHook(() => useDashboardStats())

      // Initially loading
      expect(result.current.loading).toBe(true)

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.stats).toBeDefined()
      expect(result.current.stats?.overall_score).toBe(85)
      expect(result.current.error).toBeNull()
    })

    it('handles fetch errors gracefully', async () => {
      ;(complianceApi.getStatus as jest.Mock).mockRejectedValue(new Error('Network error'))
      ;(regulationsApi.list as jest.Mock).mockRejectedValue(new Error('Network error'))
      ;(auditApi.listActions as jest.Mock).mockRejectedValue(new Error('Network error'))

      const { result } = renderHook(() => useDashboardStats())

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      expect(result.current.error).toBeTruthy()
    })
  })

  describe('useRegulations', () => {
    it('starts with loading state', () => {
      const { result } = renderHook(() => useRegulations())
      expect(result.current.loading).toBe(true)
    })
  })

  describe('useRepositories', () => {
    it('starts with loading state', () => {
      const { result } = renderHook(() => useRepositories())
      expect(result.current.loading).toBe(true)
    })
  })

  describe('useComplianceActions', () => {
    it('starts with loading state', () => {
      const { result } = renderHook(() => useComplianceActions())
      expect(result.current.loading).toBe(true)
    })
  })

  describe('useAuditTrail', () => {
    it('starts with loading state', () => {
      const { result } = renderHook(() => useAuditTrail())
      expect(result.current.loading).toBe(true)
    })
  })

  describe('useCreateRepository', () => {
    it('creates a new repository', async () => {
      const { result } = renderHook(() => useCreateRepository())

      await act(async () => {
        const created = await result.current.createRepository({
          platform: 'github',
          owner: 'acme',
          name: 'new-repo',
          profile_id: 'profile-1',
        })
        expect(created).toEqual({ id: 'new-repo-id', platform: 'github', owner: 'acme', name: 'new-repo' })
      })

      expect(repositoriesApi.create).toHaveBeenCalledWith({
        platform: 'github',
        owner: 'acme',
        name: 'new-repo',
        profile_id: 'profile-1',
      })
    })

    it('handles creation errors', async () => {
      ;(repositoriesApi.create as jest.Mock).mockRejectedValue(new Error('Repository already exists'))

      const { result } = renderHook(() => useCreateRepository())

      await expect(async () => {
        await act(async () => {
          await result.current.createRepository({
            platform: 'github',
            owner: 'acme',
            name: 'existing-repo',
            profile_id: 'profile-1',
          })
        })
      }).rejects.toThrow('Repository already exists')
    })
  })
})

describe('Error Handling', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(complianceApi.getStatus as jest.Mock).mockRejectedValue(new Error('Service unavailable'))
    ;(regulationsApi.list as jest.Mock).mockRejectedValue(new Error('Service unavailable'))
    ;(auditApi.listActions as jest.Mock).mockRejectedValue(new Error('Service unavailable'))
  })

  it('handles API errors gracefully in dashboard', async () => {
    const { result } = renderHook(() => useDashboardStats())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    // Should have an error
    expect(result.current.error).toBeTruthy()
  })
})

describe('Refetch Behavior', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(complianceApi.getStatus as jest.Mock).mockResolvedValue({
      data: { overall_score: 80 },
    })
    ;(regulationsApi.list as jest.Mock).mockResolvedValue({
      data: { items: [] },
    })
    ;(auditApi.listActions as jest.Mock).mockResolvedValue({
      data: { items: [] },
    })
  })

  it('refetches data when refetch is called', async () => {
    const { result } = renderHook(() => useDashboardStats())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    const initialCallCount = (complianceApi.getStatus as jest.Mock).mock.calls.length

    // Trigger refetch
    await act(async () => {
      await result.current.refetch()
    })

    expect((complianceApi.getStatus as jest.Mock).mock.calls.length).toBeGreaterThan(initialCallCount)
  })
})
