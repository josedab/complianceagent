import { renderHook, waitFor, act } from '@testing-library/react'

jest.mock('@/lib/api', () => {
  const actual = jest.requireActual('@/lib/api')
  return {
    ...actual,
    driftDetectionApi: {
      ...actual.driftDetectionApi,
      listEvents: jest.fn(),
    },
    apiGatewayApi: {
      ...actual.apiGatewayApi,
      getStats: jest.fn(),
      listClients: jest.fn(),
    },
    auditAutopilotApi: {
      ...actual.auditAutopilotApi,
      listFrameworks: jest.fn(),
      runGapAnalysis: jest.fn(),
    },
  }
})

import { driftDetectionApi, apiGatewayApi, auditAutopilotApi } from '@/lib/api'
import { useDriftEvents, useGatewayStats, useAuditFrameworks, useGapAnalysis } from '@/hooks/useNextgenApi'

describe('useNextgenApi hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('useDriftEvents', () => {
    it('returns real drift events from the API and never falls back to fake data', async () => {
      const events = [
        {
          id: 'de1', repo: 'acme/app', branch: 'main', drift_type: 'regression',
          severity: 'high', regulation: 'gdpr', description: 'Consent check bypassed',
          file_path: 'src/consent.ts', commit_sha: 'abc123', previous_score: 92.5,
          current_score: 78, detected_at: '2026-02-12T14:30:00Z', resolved_at: null,
        },
      ]
      ;(driftDetectionApi.listEvents as jest.Mock).mockResolvedValue({ data: events })

      const { result } = renderHook(() => useDriftEvents())

      expect(result.current.loading).toBe(true)
      await waitFor(() => expect(result.current.loading).toBe(false))

      expect(result.current.data).toEqual(events)
      expect(result.current.error).toBeNull()
    })

    it('surfaces an error and empty data instead of fabricating events on failure', async () => {
      ;(driftDetectionApi.listEvents as jest.Mock).mockRejectedValue(new Error('network down'))

      const { result } = renderHook(() => useDriftEvents())

      await waitFor(() => expect(result.current.loading).toBe(false))

      expect(result.current.error).toBeTruthy()
      expect(result.current.data).toBeNull()
    })
  })

  describe('useGatewayStats', () => {
    it('fetches gateway stats', async () => {
      const stats = {
        total_clients: 4, active_clients: 3, total_requests: 4270000,
        requests_today: 12000, rate_limited_count: 2, by_endpoint: {}, by_client: {},
      }
      ;(apiGatewayApi.getStats as jest.Mock).mockResolvedValue({ data: stats })

      const { result } = renderHook(() => useGatewayStats())
      await waitFor(() => expect(result.current.loading).toBe(false))

      expect(result.current.data).toEqual(stats)
    })
  })

  describe('useAuditFrameworks', () => {
    it('lists supported audit frameworks', async () => {
      const frameworks = [{ framework: 'soc2', control_count: 61 }]
      ;(auditAutopilotApi.listFrameworks as jest.Mock).mockResolvedValue({ data: frameworks })

      const { result } = renderHook(() => useAuditFrameworks())
      await waitFor(() => expect(result.current.loading).toBe(false))

      expect(result.current.data).toEqual(frameworks)
    })

    it('defaults to an empty list rather than mock data when the API returns nothing', async () => {
      ;(auditAutopilotApi.listFrameworks as jest.Mock).mockResolvedValue({ data: null })

      const { result } = renderHook(() => useAuditFrameworks())
      await waitFor(() => expect(result.current.loading).toBe(false))

      expect(result.current.data).toEqual([])
    })
  })

  describe('useGapAnalysis (mutation)', () => {
    it('runs a gap analysis for the given framework', async () => {
      const gapResult = {
        id: 'ga1', framework: 'soc2', total_controls: 61, controls_met: 48,
        controls_partial: 8, controls_missing: 5, readiness_score: 78.7,
        critical_gaps: [], estimated_remediation_hours: 12,
      }
      ;(auditAutopilotApi.runGapAnalysis as jest.Mock).mockResolvedValue({ data: gapResult })

      const { result } = renderHook(() => useGapAnalysis())
      let returned
      await act(async () => {
        returned = await result.current.mutate('soc2')
      })

      expect(auditAutopilotApi.runGapAnalysis).toHaveBeenCalledWith('soc2')
      expect(returned).toEqual(gapResult)
    })
  })
})
