'use client'

import { useState } from 'react'
import { Lock, FileCheck, Eye, Shield, Download } from 'lucide-react'
import { useEvidence, useAuditReport, useVerifyChain, useCreateAuditorSession } from '@/hooks/useNextgenApi'
import type { ControlFramework, AuditorSession } from '@/types/nextgen'

const frameworkLabels: Record<ControlFramework, string> = {
  soc2: 'SOC 2', iso27001: 'ISO 27001', hipaa: 'HIPAA', pci_dss: 'PCI-DSS', gdpr: 'GDPR', nist: 'NIST',
}

export default function EvidenceVaultDashboard() {
  const [selectedFramework, setSelectedFramework] = useState<ControlFramework | 'all'>('all')
  const reportFramework: ControlFramework = selectedFramework === 'all' ? 'soc2' : selectedFramework

  const { data: evidence, loading: evidenceLoading, error: evidenceError, refetch: refetchEvidence } =
    useEvidence(selectedFramework === 'all' ? undefined : selectedFramework)
  const { data: report, loading: reportLoading, error: reportError } = useAuditReport(reportFramework)
  const { data: chain, loading: chainLoading, error: chainError } = useVerifyChain(reportFramework)
  const { mutate: createSession, loading: sessionCreating } = useCreateAuditorSession()
  const [session, setSession] = useState<AuditorSession | null>(null)
  const [sessionError, setSessionError] = useState<string | null>(null)

  const loading = evidenceLoading || reportLoading || chainLoading
  const error = evidenceError || reportError || chainError

  async function handleInviteAuditor() {
    setSessionError(null)
    try {
      const result = await createSession({ auditor_email: 'auditor@example.com', auditor_name: 'External Auditor' })
      setSession(result)
    } catch {
      setSessionError('Failed to create auditor session')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}
        </div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Evidence Vault & Auditor Portal</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading evidence vault: {error.message}</p>
          <button onClick={refetchEvidence} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const items = evidence || []
  const filtered = selectedFramework === 'all' ? items : items.filter(e => e.framework === selectedFramework)
  const frameworks = Array.from(new Set(items.map(e => e.framework)))
  const evidenceByFramework = frameworks.reduce<Record<string, number>>((acc, fw) => {
    acc[fw] = items.filter(e => e.framework === fw).length
    return acc
  }, {})

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
          <p className="mt-2 text-3xl font-bold text-gray-900">{items.length}</p>
          <p className="mt-1 text-sm text-gray-500">{frameworks.length} frameworks covered</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between"><p className="text-sm font-medium text-gray-500">{frameworkLabels[reportFramework]} Coverage</p><Shield className="h-5 w-5 text-green-600" /></div>
          <p className="mt-2 text-3xl font-bold text-green-600">{report ? `${report.coverage_percentage}%` : 'N/A'}</p>
          <p className="mt-1 text-sm text-gray-500">{report ? `${report.controls_with_evidence}/${report.total_controls} controls` : 'No report yet'}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between"><p className="text-sm font-medium text-gray-500">Chain Integrity</p><Lock className="h-5 w-5 text-purple-600" /></div>
          <p className={`mt-2 text-3xl font-bold ${chain?.verified ? 'text-purple-600' : 'text-gray-400'}`}>{chain?.verified ? 'Verified' : 'Unverified'}</p>
          <p className={`mt-1 text-sm ${chain?.verified ? 'text-green-500' : 'text-gray-400'}`}>{chain?.verified ? 'Hash chain valid ✓' : 'No verification data'}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between"><p className="text-sm font-medium text-gray-500">Auditor Sessions</p><Eye className="h-5 w-5 text-orange-600" /></div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{session ? 1 : 0}</p>
          {session ? (
            <p className="mt-1 text-sm text-gray-500">{session.auditor_name}</p>
          ) : (
            <button
              onClick={handleInviteAuditor}
              disabled={sessionCreating}
              className="mt-1 text-sm text-primary-600 hover:underline disabled:opacity-50"
            >
              {sessionCreating ? 'Inviting…' : 'Invite auditor'}
            </button>
          )}
          {sessionError && <p className="mt-1 text-xs text-red-600">{sessionError}</p>}
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
        {filtered.length === 0 ? (
          <p className="text-gray-500 text-sm">No evidence recorded yet.</p>
        ) : (
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
        )}
      </div>

      {/* Control Mapping (derived from real evidence, not fabricated) */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">📋 Evidence by Framework</h2>
        <p className="text-sm text-gray-500 mb-4">Evidence items recorded per framework</p>
        {frameworks.length === 0 ? (
          <p className="text-gray-500 text-sm">No evidence recorded yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {frameworks.map(fw => (
              <div key={fw} className="p-4 rounded-lg bg-gray-50 border border-gray-200">
                <p className="text-sm font-medium text-gray-700">{frameworkLabels[fw as ControlFramework] || fw}</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">{evidenceByFramework[fw]}</p>
                <p className="text-xs text-gray-500">evidence items</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
