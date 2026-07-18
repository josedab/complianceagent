import { render, screen, fireEvent } from '@testing-library/react'
import APIGatewayDashboard from '@/components/nextgen/APIGatewayDashboard'
import { useGatewayClients, useGatewayStats } from '@/hooks/useNextgenApi'

jest.mock('@/hooks/useNextgenApi', () => ({
  useGatewayClients: jest.fn(),
  useGatewayStats: jest.fn(),
}))

describe('APIGatewayDashboard', () => {
  it('shows a loading skeleton while data is in flight', () => {
    ;(useGatewayClients as jest.Mock).mockReturnValue({ data: null, loading: true, error: null, refetch: jest.fn() })
    ;(useGatewayStats as jest.Mock).mockReturnValue({ data: null, loading: true, error: null, refetch: jest.fn() })

    render(<APIGatewayDashboard />)

    expect(screen.queryByText('OAuth Clients')).not.toBeInTheDocument()
  })

  it('shows an honest error banner and never renders fabricated clients on failure', () => {
    const refetch = jest.fn()
    ;(useGatewayClients as jest.Mock).mockReturnValue({ data: null, loading: false, error: { message: 'Request failed' }, refetch })
    ;(useGatewayStats as jest.Mock).mockReturnValue({ data: null, loading: false, error: null, refetch: jest.fn() })

    render(<APIGatewayDashboard />)

    expect(screen.getByText(/Error loading API Gateway/)).toBeInTheDocument()
    expect(screen.queryByText('ComplianceBot Pro')).not.toBeInTheDocument()

    fireEvent.click(screen.getByText('Retry'))
    expect(refetch).toHaveBeenCalled()
  })

  it('renders an honest empty state when there are no clients yet', () => {
    ;(useGatewayClients as jest.Mock).mockReturnValue({ data: [], loading: false, error: null, refetch: jest.fn() })
    ;(useGatewayStats as jest.Mock).mockReturnValue({
      data: { total_clients: 0, active_clients: 0, total_requests: 0, requests_today: 0, rate_limited_count: 0, by_endpoint: {}, by_client: {} },
      loading: false, error: null, refetch: jest.fn(),
    })

    render(<APIGatewayDashboard />)

    expect(screen.getByText('No clients registered yet.')).toBeInTheDocument()
  })

  it('renders real client data from the API', () => {
    ;(useGatewayClients as jest.Mock).mockReturnValue({
      data: [{ id: 'c1', name: 'Real Client', description: '', api_key: 'key', scopes: ['read'], rate_limit_per_minute: 60, webhook_url: '', active: true, created_at: null }],
      loading: false, error: null, refetch: jest.fn(),
    })
    ;(useGatewayStats as jest.Mock).mockReturnValue({
      data: { total_clients: 1, active_clients: 1, total_requests: 100, requests_today: 10, rate_limited_count: 0, by_endpoint: {}, by_client: {} },
      loading: false, error: null, refetch: jest.fn(),
    })

    render(<APIGatewayDashboard />)

    expect(screen.getByText('Real Client')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
  })
})
