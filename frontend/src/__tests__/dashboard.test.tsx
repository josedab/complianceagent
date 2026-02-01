import { render, screen } from '@testing-library/react'
import DashboardPage from '@/app/dashboard/page'

// Mock the hooks directly
jest.mock('@/hooks/useApi', () => ({
  useDashboardStats: jest.fn(() => ({
    stats: {
      overall_score: 92,
      compliant: 138,
      partial: 5,
      non_compliant: 7,
      pending: 5,
      trend_percentage: 2.3,
    },
    frameworkStatuses: [
      { framework: 'GDPR', name: 'GDPR', status: 'COMPLIANT', score: 95, requirements_total: 50, requirements_compliant: 48 },
      { framework: 'CCPA', name: 'CCPA', status: 'PARTIAL_COMPLIANCE', score: 85, requirements_total: 30, requirements_compliant: 25 },
    ],
    recentActivity: [],
    deadlines: [],
    loading: false,
    error: null,
    refetch: jest.fn(),
  })),
}))

describe('Dashboard Page', () => {
  it('renders the compliance dashboard', () => {
    render(<DashboardPage />)
    
    // Check for main heading
    expect(screen.getByText('Compliance Dashboard')).toBeInTheDocument()
    
    // Check for stat cards
    expect(screen.getByText('Overall Compliance')).toBeInTheDocument()
    expect(screen.getByText('Compliant Requirements')).toBeInTheDocument()
    expect(screen.getByText('Action Required')).toBeInTheDocument()
    expect(screen.getByText('Pending Review')).toBeInTheDocument()
  })

  it('displays compliance score', () => {
    render(<DashboardPage />)
    
    // The mock data shows 92% compliance
    expect(screen.getByText('92%')).toBeInTheDocument()
  })

  it('shows recent activity section', () => {
    render(<DashboardPage />)
    
    expect(screen.getByText('Recent Activity')).toBeInTheDocument()
  })

  it('displays framework compliance breakdown', () => {
    render(<DashboardPage />)
    
    expect(screen.getByText('Framework Compliance')).toBeInTheDocument()
    // GDPR comes from the mocked regulations
    expect(screen.getByText('GDPR')).toBeInTheDocument()
  })
})
