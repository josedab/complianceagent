import { render, screen } from '@testing-library/react'
import DriftDetectionDashboard from '@/components/nextgen/DriftDetectionDashboard'
import { useDriftEvents, useDriftAlerts } from '@/hooks/useNextgenApi'

jest.mock('@/hooks/useNextgenApi', () => ({
  useDriftEvents: jest.fn(),
  useDriftAlerts: jest.fn(),
}))

describe('DriftDetectionDashboard', () => {
  it('never renders fabricated drift events after an API failure', () => {
    ;(useDriftEvents as jest.Mock).mockReturnValue({ data: null, loading: false, error: { message: 'boom' }, refetch: jest.fn() })
    ;(useDriftAlerts as jest.Mock).mockReturnValue({ data: null, loading: false, error: null, refetch: jest.fn() })

    render(<DriftDetectionDashboard />)

    expect(screen.getByText(/Error loading drift events/)).toBeInTheDocument()
    expect(screen.queryByText('GDPR Fine Escalation')).not.toBeInTheDocument()
    expect(screen.queryByText('Using demo data')).not.toBeInTheDocument()
  })

  it('renders an honest empty state with no events', () => {
    ;(useDriftEvents as jest.Mock).mockReturnValue({ data: [], loading: false, error: null, refetch: jest.fn() })
    ;(useDriftAlerts as jest.Mock).mockReturnValue({ data: [], loading: false, error: null, refetch: jest.fn() })

    render(<DriftDetectionDashboard />)

    expect(screen.getByText('No drift events detected.')).toBeInTheDocument()
  })

  it('renders real drift events from the API', () => {
    ;(useDriftEvents as jest.Mock).mockReturnValue({
      data: [{
        id: 'de1', repo: 'acme/app', branch: 'main', drift_type: 'regression', severity: 'critical',
        regulation: 'gdpr', description: 'Consent check bypassed', file_path: 'x.ts', commit_sha: 'abc',
        previous_score: 92.5, current_score: 70, detected_at: '2026-02-13T08:00:00Z', resolved_at: null,
      }],
      loading: false, error: null, refetch: jest.fn(),
    })
    ;(useDriftAlerts as jest.Mock).mockReturnValue({ data: [{ channel: 'email', status: 'active' }], loading: false, error: null, refetch: jest.fn() })

    render(<DriftDetectionDashboard />)

    expect(screen.getByText('Consent check bypassed')).toBeInTheDocument()
    expect(screen.getByText('acme/app')).toBeInTheDocument()
  })
})
