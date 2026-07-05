'use client'

import { Siren, Clock, FileCheck, Bell } from 'lucide-react'
import { usePlaybooks, useIncidents } from '@/hooks/useNextgenApi'
import type { PlaybookRecord, IncidentRecord } from '@/types/nextgen'

const severityColors: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  low: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
}

export default function IncidentPlaybookDashboard() {
  const { data: livePlaybooks, loading: pbLoading, error: pbError, refetch: refetchPb } = usePlaybooks()
  const { data: liveIncidents, loading: incLoading, error: incError, refetch: refetchInc } = useIncidents()

  const loading = pbLoading || incLoading
  const error = pbError || incError

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
        </div>
        <div className="card h-64 animate-pulse bg-gray-100" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading Incident Playbooks: {error.message}</p>
        <button onClick={() => { refetchPb(); refetchInc(); }} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const playbooks = livePlaybooks ?? []
  const incidents = liveIncidents ?? []
  const activeIncidents = incidents.filter(i => i.status !== 'resolved')
  const totalAffected = incidents.reduce((sum, i) => sum + i.affected_data_subjects, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Incident Response Compliance Playbook</h1>
        <p className="text-gray-500">Pre-built playbooks with jurisdiction-specific notification timelines</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Playbooks</p>
            <Siren className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{playbooks.length}</p>
          <p className="mt-1 text-sm text-gray-500">Available playbooks</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Active Incidents</p>
            <Clock className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{activeIncidents.length}</p>
          <p className="mt-1 text-sm text-red-500">In progress</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Total Incidents</p>
            <FileCheck className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">{incidents.length}</p>
          <p className="mt-1 text-sm text-gray-500">All tracked incidents</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Affected Subjects</p>
            <Bell className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{totalAffected.toLocaleString()}</p>
          <p className="mt-1 text-sm text-gray-500">Data subjects impacted</p>
        </div>
      </div>

      {/* Active Incidents */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Siren className="h-5 w-5 text-red-500" />
          <h2 className="text-lg font-semibold text-gray-900">Active Incidents</h2>
        </div>
        {activeIncidents.length === 0 ? (
          <p className="text-gray-500 text-sm">No active incidents.</p>
        ) : (
          <div className="space-y-3">
            {activeIncidents.map((inc: IncidentRecord) => {
              const colors = severityColors[inc.severity] ?? severityColors.medium
              return (
                <div key={inc.id} className={`p-4 rounded-lg border ${colors.border} ${colors.bg}`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${colors.text} bg-white`}>{inc.severity}</span>
                      <span className="font-medium text-gray-900">{inc.title}</span>
                    </div>
                    <span className="text-sm text-gray-500">{inc.started_at ? new Date(inc.started_at).toLocaleString() : '—'}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>{inc.incident_type.replace(/_/g, ' ')}</span>
                    <span>{inc.jurisdictions_affected.join(', ')}</span>
                    <span>{inc.affected_data_subjects.toLocaleString()} subjects affected</span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Playbooks */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <FileCheck className="h-5 w-5 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-900">Playbooks</h2>
        </div>
        {playbooks.length === 0 ? (
          <p className="text-gray-500 text-sm">No playbooks available yet.</p>
        ) : (
          <div className="space-y-3">
            {playbooks.map((pb: PlaybookRecord) => (
              <div key={pb.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-gray-900">{pb.name}</span>
                  <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700">
                    {pb.jurisdictions.join(', ')}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>{pb.incident_type.replace(/_/g, ' ')}</span>
                  <span>{pb.steps.length} steps</span>
                  <span>{pb.evidence_checklist.length} checklist items</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
