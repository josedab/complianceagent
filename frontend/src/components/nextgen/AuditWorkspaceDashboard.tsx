'use client'

import { Shield, CheckCircle, AlertTriangle, ArrowRight, ClipboardCheck } from 'lucide-react'
import { useState } from 'react'

type Phase = 'gap_analysis' | 'evidence_collection' | 'remediation' | 'review' | 'audit_ready'

import type { LucideIcon } from 'lucide-react'

const PHASES: { key: Phase; label: string; icon: LucideIcon }[] = [
  { key: 'gap_analysis', label: 'Gap Analysis', icon: ClipboardCheck },
  { key: 'evidence_collection', label: 'Evidence Collection', icon: Shield },
  { key: 'remediation', label: 'Remediation', icon: AlertTriangle },
  { key: 'review', label: 'Review', icon: CheckCircle },
  { key: 'audit_ready', label: 'Audit Ready', icon: CheckCircle },
]

const MOCK_GAPS = [
  { control_id: 'CC6.1', name: 'Logical Access', status: 'verified', severity: 'low', evidence: 3, required: 3 },
  { control_id: 'CC6.6', name: 'Encryption in Transit', status: 'verified', severity: 'low', evidence: 2, required: 2 },
  { control_id: 'CC6.7', name: 'Encryption at Rest', status: 'in_progress', severity: 'medium', evidence: 1, required: 2 },
  { control_id: 'CC7.1', name: 'Vulnerability Management', status: 'in_progress', severity: 'medium', evidence: 1, required: 2 },
  { control_id: 'CC7.2', name: 'Security Monitoring', status: 'not_started', severity: 'high', evidence: 0, required: 3 },
  { control_id: 'CC7.3', name: 'Incident Response', status: 'not_started', severity: 'high', evidence: 0, required: 3 },
  { control_id: 'CC8.1', name: 'Change Management', status: 'verified', severity: 'low', evidence: 3, required: 3 },
  { control_id: 'A1.2', name: 'Disaster Recovery', status: 'not_started', severity: 'high', evidence: 0, required: 3 },
]

const statusColors: Record<string, { bg: string; text: string }> = {
  verified: { bg: 'bg-green-50', text: 'text-green-700' },
  in_progress: { bg: 'bg-yellow-50', text: 'text-yellow-700' },
  not_started: { bg: 'bg-red-50', text: 'text-red-700' },
}

export default function AuditWorkspaceDashboard() {
  const [currentPhase, setCurrentPhase] = useState<Phase>('gap_analysis')
  const currentIdx = PHASES.findIndex(p => p.key === currentPhase)

  const verified = MOCK_GAPS.filter(g => g.status === 'verified').length
  const total = MOCK_GAPS.length
  const readiness = Math.round((verified / total) * 100)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Workspace</h1>
        <p className="text-gray-500">SOC 2 Type II — Self-service audit preparation</p>
      </div>

      {/* Phase stepper */}
      <div className="card">
        <div className="flex items-center justify-between">
          {PHASES.map((phase, i) => {
            const Icon = phase.icon
            const isActive = i === currentIdx
            const isDone = i < currentIdx
            return (
              <div key={phase.key} className="flex items-center">
                <div className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                  isActive ? 'bg-blue-100 text-blue-700' : isDone ? 'bg-green-50 text-green-600' : 'text-gray-400'
                }`} onClick={() => setCurrentPhase(phase.key)}>
                  <Icon className="h-4 w-4" />
                  <span className="text-sm font-medium">{phase.label}</span>
                </div>
                {i < PHASES.length - 1 && <ArrowRight className="h-4 w-4 mx-2 text-gray-300" />}
              </div>
            )
          })}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card text-center py-6">
          <p className="text-sm font-medium text-gray-500">Audit Readiness</p>
          <p className={`text-4xl font-bold mt-2 ${readiness >= 80 ? 'text-green-600' : readiness >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
            {readiness}%
          </p>
        </div>
        <div className="card text-center py-6">
          <p className="text-sm font-medium text-gray-500">Controls Verified</p>
          <p className="text-4xl font-bold mt-2 text-gray-900">{verified}/{total}</p>
        </div>
        <div className="card text-center py-6">
          <p className="text-sm font-medium text-gray-500">Gaps Remaining</p>
          <p className="text-4xl font-bold mt-2 text-red-600">{total - verified}</p>
        </div>
      </div>

      {/* Control gaps */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Control Status</h2>
        <div className="space-y-2">
          {MOCK_GAPS.map(gap => {
            const colors = statusColors[gap.status]
            return (
              <div key={gap.control_id} className={`p-3 rounded-lg border ${colors.bg}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-mono text-sm text-gray-500">{gap.control_id}</span>
                    <span className="mx-2 text-gray-300">|</span>
                    <span className="font-medium text-gray-900">{gap.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-500">{gap.evidence}/{gap.required} evidence</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${colors.bg} ${colors.text} border`}>
                      {gap.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
