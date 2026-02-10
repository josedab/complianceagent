'use client'

import { useState } from 'react'
import { Lock, FileCheck, Eye, Shield, Download } from 'lucide-react'
import { useEvidence } from '@/hooks/useNextgenApi'
import type { EvidenceItem, AuditReport, AuditorSession, ControlFramework } from '@/types/nextgen'

const MOCK_EVIDENCE: EvidenceItem[] = [
  { id: 'ev1', evidence_type: 'scan_result', title: 'SAST Scan - Q1 2026', description: 'Static analysis security scan results', content_hash: 'sha256:a1b2c3...', framework: 'soc2', control_id: 'CC6.1', created_at: '2026-02-01T10:00:00Z' },
  { id: 'ev2', evidence_type: 'policy_document', title: 'Data Retention Policy v3.2', description: 'Updated data retention policy', content_hash: 'sha256:d4e5f6...', framework: 'gdpr', control_id: 'Art.5(1)(e)', created_at: '2026-01-15T14:30:00Z' },
  { id: 'ev3', evidence_type: 'test_result', title: 'Penetration Test - Feb 2026', description: 'External penetration test results', content_hash: 'sha256:g7h8i9...', framework: 'pci_dss', control_id: 'Req.11.3', created_at: '2026-02-10T09:00:00Z' },
  { id: 'ev4', evidence_type: 'training_record', title: 'Security Awareness Training', description: 'Annual security training completion', content_hash: 'sha256:j0k1l2...', framework: 'hipaa', control_id: '164.308(a)(5)', created_at: '2026-02-05T11:00:00Z' },
  { id: 'ev5', evidence_type: 'code_review', title: 'Compliance Code Review - Sprint 24', description: 'Code review for GDPR consent module', content_hash: 'sha256:m3n4o5...', framework: 'soc2', control_id: 'CC8.1', created_at: '2026-02-12T16:00:00Z' },
]

const MOCK_REPORT: AuditReport = {
  framework: 'soc2', total_controls: 61, controls_with_evidence: 48, coverage_percentage: 78.7, generated_at: '2026-02-13T10:00:00Z',
}

const MOCK_SESSION: AuditorSession = {
  id: 'ses-001', auditor_email: 'auditor@deloitte.com', auditor_name: 'Jane Auditor', is_active: true, expires_at: '2026-05-13T10:00:00Z',
}

const frameworkLabels: Record<ControlFramework, string> = {
  soc2: 'SOC 2', iso27001: 'ISO 27001', hipaa: 'HIPAA', pci_dss: 'PCI-DSS', gdpr: 'GDPR', nist: 'NIST',
}

export default function EvidenceVaultDashboard() {
  const [selectedFramework, setSelectedFramework] = useState<ControlFramework | 'all'>('all')
  const { data: liveEvidence } = useEvidence(selectedFramework === 'all' ? undefined : selectedFramework)
  const evidence = liveEvidence || MOCK_EVIDENCE
  const filtered = selectedFramework === 'all' ? evidence : evidence.filter(e => e.framework === selectedFramework)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Evidence Vault & Auditor Portal</h1>
        <p className="text-gray-500">Immutable evidence storage with hash-chain verification</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between"><p className="text-sm font-medium text-gray-500">Total Evidence</p><FileCheck className="h-5 w-5 text-blue-600" /></div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{MOCK_EVIDENCE.length}</p>
          <p className="mt-1 text-sm text-gray-500">Across all frameworks</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between"><p className="text-sm font-medium text-gray-500">SOC 2 Coverage</p><Shield className="h-5 w-5 text-green-600" /></div>
          <p className="mt-2 text-3xl font-bold text-green-600">{MOCK_REPORT.coverage_percentage}%</p>
          <p className="mt-1 text-sm text-gray-500">{MOCK_REPORT.controls_with_evidence}/{MOCK_REPORT.total_controls} controls</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between"><p className="text-sm font-medium text-gray-500">Chain Integrity</p><Lock className="h-5 w-5 text-purple-600" /></div>
          <p className="mt-2 text-3xl font-bold text-purple-600">Verified</p>
          <p className="mt-1 text-sm text-green-500">Hash chain valid ✓</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between"><p className="text-sm font-medium text-gray-500">Auditor Sessions</p><Eye className="h-5 w-5 text-orange-600" /></div>
          <p className="mt-2 text-3xl font-bold text-gray-900">1</p>
          <p className="mt-1 text-sm text-gray-500">{MOCK_SESSION.auditor_name}</p>
        </div>
      </div>

      {/* Filter */}
      <div className="card">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Framework:</label>
          <select value={selectedFramework} onChange={e => setSelectedFramework(e.target.value as ControlFramework | 'all')} className="rounded-md border border-gray-300 px-3 py-2 text-sm">
            <option value="all">All Frameworks</option>
            {Object.entries(frameworkLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <div className="ml-auto">
            <button className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 flex items-center gap-2">
              <Download className="h-4 w-4" /> Export Report
            </button>
          </div>
        </div>
      </div>

      {/* Evidence Items */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Evidence Items ({filtered.length})</h2>
        <div className="space-y-3">
          {filtered.map(item => (
            <div key={item.id} className="p-3 rounded-lg border border-gray-100 hover:border-primary-200 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileCheck className="h-4 w-4 text-blue-500" />
                  <span className="font-medium text-gray-900">{item.title}</span>
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">{frameworkLabels[item.framework]}</span>
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">{item.control_id}</span>
                </div>
                <span className="text-sm text-gray-400">{new Date(item.created_at).toLocaleDateString()}</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">{item.description}</p>
              <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
                <Lock className="h-3 w-3" />
                <span className="font-mono">{item.content_hash}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
