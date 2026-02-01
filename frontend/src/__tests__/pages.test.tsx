import React from 'react'
import { render, screen } from '@testing-library/react'

// Mock the API hooks directly to avoid complex mocking of axios
jest.mock('@/hooks/useApi', () => ({
  useRegulations: jest.fn(() => ({
    data: [
      { id: '1', name: 'General Data Protection Regulation', short_name: 'GDPR', framework: 'GDPR', jurisdiction: 'EU', compliance_score: 95 },
      { id: '2', name: 'California Consumer Privacy Act', short_name: 'CCPA', framework: 'CCPA', jurisdiction: 'US-CA', compliance_score: 88 },
      { id: '3', name: 'EU AI Act', short_name: 'EU AI Act', framework: 'EU_AI_ACT', jurisdiction: 'EU', compliance_score: 72 },
      { id: '4', name: 'HIPAA', short_name: 'HIPAA', framework: 'HIPAA', jurisdiction: 'US-Federal', compliance_score: 90 },
    ],
    loading: false,
    error: null,
    refetch: jest.fn(),
  })),
  useRepositories: jest.fn(() => ({
    data: [
      { id: '1', platform: 'github', owner: 'acme', name: 'backend-api', compliance_score: 92, full_name: 'acme/backend-api' },
      { id: '2', platform: 'github', owner: 'acme', name: 'frontend-app', compliance_score: 88, full_name: 'acme/frontend-app' },
    ],
    loading: false,
    error: null,
    refetch: jest.fn(),
  })),
  useCreateRepository: jest.fn(() => ({
    createRepository: jest.fn(),
    loading: false,
    error: null,
  })),
  useAnalyzeRepository: jest.fn(() => ({
    analyzeRepository: jest.fn(),
    loading: false,
    error: null,
  })),
  useComplianceActions: jest.fn(() => ({
    data: [
      { id: '1', title: 'Add Data Subject Access Request Handler', status: 'pending', priority: 'high', requirement_id: 'req-1', organization_id: 'org-1', repository_id: 'repo-1', description: 'Implement DSAR handler', affected_files: [], created_at: '2026-01-28T10:00:00Z', updated_at: '2026-01-28T10:00:00Z' },
      { id: '2', title: 'Implement Consent Withdrawal Mechanism', status: 'in_progress', priority: 'medium', requirement_id: 'req-2', organization_id: 'org-1', repository_id: 'repo-1', description: 'Implement consent withdrawal', affected_files: [], created_at: '2026-01-28T11:00:00Z', updated_at: '2026-01-28T11:00:00Z' },
    ],
    loading: false,
    error: null,
    refetch: jest.fn(),
  })),
  useUpdateAction: jest.fn(() => ({
    updateAction: jest.fn(),
    loading: false,
    error: null,
  })),
  useAuditTrail: jest.fn(() => ({
    data: [
      { id: '1', event_type: 'requirement_extracted', description: 'Requirement Extracted', created_at: '2026-01-28T10:00:00Z', organization_id: 'org-1', actor_type: 'system', resource_type: 'requirement', resource_id: 'req-12345678', metadata: {}, hash: 'abc123' },
      { id: '2', event_type: 'mapping_created', description: 'Mapping Created', created_at: '2026-01-28T11:00:00Z', organization_id: 'org-1', actor_type: 'ai', resource_type: 'mapping', resource_id: 'map-12345678', metadata: {}, hash: 'def456' },
      { id: '3', event_type: 'code_generated', description: 'Code Generated', created_at: '2026-01-28T12:00:00Z', organization_id: 'org-1', actor_type: 'ai', resource_type: 'code', resource_id: 'code-12345678', metadata: {}, hash: 'ghi789' },
    ],
    loading: false,
    error: null,
    refetch: jest.fn(),
  })),
}))

import RegulationsPage from '@/app/dashboard/regulations/page'

describe('Regulations Page', () => {
  it('renders the regulations list', () => {
    render(<RegulationsPage />)
    
    // Check for main heading
    expect(screen.getByRole('heading', { name: 'Regulations' })).toBeInTheDocument()
    
    // Check for filter controls
    expect(screen.getByPlaceholderText('Search regulations...')).toBeInTheDocument()
  })

  it('displays regulation cards', () => {
    render(<RegulationsPage />)
    
    // Use getAllByText to handle multiple matches (dropdown + card)
    const gdprElements = screen.getAllByText('GDPR')
    expect(gdprElements.length).toBeGreaterThan(0)
    
    const ccpaElements = screen.getAllByText('CCPA')
    expect(ccpaElements.length).toBeGreaterThan(0)
  })

  it('displays jurisdiction information', () => {
    render(<RegulationsPage />)
    
    // Check that jurisdictions appear in the regulation cards
    expect(screen.getByText('US-CA')).toBeInTheDocument()
    expect(screen.getByText('US-Federal')).toBeInTheDocument()
  })
})


describe('Repositories Page', () => {
  let RepositoriesPage: React.ComponentType
  
  beforeAll(async () => {
    const mod = await import('@/app/dashboard/repositories/page')
    RepositoriesPage = mod.default
  })

  it('renders the repositories list', () => {
    render(<RepositoriesPage />)
    
    expect(screen.getByRole('heading', { name: 'Repositories' })).toBeInTheDocument()
    expect(screen.getByText('Add Repository')).toBeInTheDocument()
  })

  it('displays repository cards', () => {
    render(<RepositoriesPage />)
    
    expect(screen.getByText('acme/backend-api')).toBeInTheDocument()
    expect(screen.getByText('acme/frontend-app')).toBeInTheDocument()
  })
})


describe('Actions Page', () => {
  let ActionsPage: React.ComponentType
  
  beforeAll(async () => {
    const mod = await import('@/app/dashboard/actions/page')
    ActionsPage = mod.default
  })

  it('renders the actions list', () => {
    render(<ActionsPage />)
    
    expect(screen.getByRole('heading', { name: 'Compliance Actions' })).toBeInTheDocument()
  })

  it('displays status statistics', () => {
    render(<ActionsPage />)
    
    expect(screen.getByText('Pending Approval')).toBeInTheDocument()
    // Use getAllByText for elements that may appear in dropdown and cards
    const inProgressElements = screen.getAllByText('In Progress')
    expect(inProgressElements.length).toBeGreaterThan(0)
    const completedElements = screen.getAllByText('Completed')
    expect(completedElements.length).toBeGreaterThan(0)
  })

  it('shows action cards with details', () => {
    render(<ActionsPage />)
    
    expect(screen.getByText('Add Data Subject Access Request Handler')).toBeInTheDocument()
    expect(screen.getByText('Implement Consent Withdrawal Mechanism')).toBeInTheDocument()
  })
})


describe('Audit Page', () => {
  let AuditPage: React.ComponentType
  
  beforeAll(async () => {
    const mod = await import('@/app/dashboard/audit/page')
    AuditPage = mod.default
  })

  it('renders the audit trail', () => {
    render(<AuditPage />)
    
    expect(screen.getByRole('heading', { name: 'Audit Trail' })).toBeInTheDocument()
  })

  it('shows hash chain verification status', () => {
    render(<AuditPage />)
    
    expect(screen.getByText('Hash Chain Verified')).toBeInTheDocument()
  })

  it('displays audit entries with event types', () => {
    render(<AuditPage />)
    
    // Use getAllByText since event types appear in both dropdowns and entries
    const extractedElements = screen.getAllByText('Requirement Extracted')
    expect(extractedElements.length).toBeGreaterThan(0)
    
    const mappingElements = screen.getAllByText('Mapping Created')
    expect(mappingElements.length).toBeGreaterThan(0)
    
    const codeElements = screen.getAllByText('Code Generated')
    expect(codeElements.length).toBeGreaterThan(0)
  })

  it('has export functionality', () => {
    render(<AuditPage />)
    
    expect(screen.getByText('Export Report')).toBeInTheDocument()
  })
})
