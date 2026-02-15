'use client'

import { Siren, Clock, FileCheck, Bell } from 'lucide-react'
import { usePlaybooks, useIncidents } from '@/hooks/useNextgenApi'
import type { PlaybookRecord, IncidentRecord } from '@/types/nextgen'

interface PlaybookDisplay extends PlaybookRecord {
  jurisdiction: string;
  notification_deadline_hours: number;
  last_updated: string;
}

interface IncidentDisplay extends IncidentRecord {
  playbook: string;
  notifications_sent: number;
  response_hours: number;
}

const MOCK_PLAYBOOKS: PlaybookDisplay[] = [
  { id: 'pb1', name: 'GDPR Breach Response', incident_type: 'data_breach', description: 'GDPR breach response playbook', steps: [{},{},{},{},{},{},{},{}], notification_requirements: [], evidence_checklist: [], jurisdictions: ['EU'], jurisdiction: 'EU', notification_deadline_hours: 72, last_updated: '2026-03-10T10:00:00Z' },
  { id: 'pb2', name: 'HIPAA Incident Protocol', incident_type: 'data_breach', description: 'HIPAA incident protocol', steps: [{},{},{},{},{},{},{},{},{},{}], notification_requirements: [], evidence_checklist: [], jurisdictions: ['US'], jurisdiction: 'US', notification_deadline_hours: 60, last_updated: '2026-03-09T14:00:00Z' },
  { id: 'pb3', name: 'PCI DSS Compromise Response', incident_type: 'security_compromise', description: 'PCI DSS compromise response', steps: [{},{},{},{},{},{},{},{},{},{},{},{}], notification_requirements: [], evidence_checklist: [], jurisdictions: ['Global'], jurisdiction: 'Global', notification_deadline_hours: 24, last_updated: '2026-03-08T09:00:00Z' },
  { id: 'pb4', name: 'SOX Material Weakness', incident_type: 'material_weakness', description: 'SOX material weakness playbook', steps: [{},{},{},{},{},{}], notification_requirements: [], evidence_checklist: [], jurisdictions: ['US'], jurisdiction: 'US', notification_deadline_hours: 48, last_updated: '2026-03-07T16:00:00Z' },
  { id: 'pb5', name: 'CCPA Data Breach Notice', incident_type: 'data_breach', description: 'CCPA data breach notice', steps: [{},{},{},{},{},{},{}], notification_requirements: [], evidence_checklist: [], jurisdictions: ['California'], jurisdiction: 'California', notification_deadline_hours: 72, last_updated: '2026-03-06T11:00:00Z' },
  { id: 'pb6', name: 'NIS2 Incident Report', incident_type: 'incident_report', description: 'NIS2 incident report', steps: [{},{},{},{},{},{},{},{},{}], notification_requirements: [], evidence_checklist: [], jurisdictions: ['EU'], jurisdiction: 'EU', notification_deadline_hours: 24, last_updated: '2026-03-05T13:00:00Z' },
]

const MOCK_INCIDENTS: IncidentDisplay[] = [
  { id: 'inc1', playbook_id: 'pb1', incident_type: 'data_breach', severity: 'high', title: 'Unauthorized data access detected', description: 'Unauthorized access detected', status: 'in_progress', affected_data_subjects: 0, jurisdictions_affected: ['EU'], started_at: '2026-03-12T06:00:00Z', resolved_at: null, playbook: 'GDPR Breach Response', notifications_sent: 5, response_hours: 3.2 },
  { id: 'inc2', playbook_id: 'pb2', incident_type: 'data_breach', severity: 'critical', title: 'PHI exposure in staging logs', description: 'PHI exposure in staging', status: 'in_progress', affected_data_subjects: 0, jurisdictions_affected: ['US'], started_at: '2026-03-11T22:00:00Z', resolved_at: null, playbook: 'HIPAA Incident Protocol', notifications_sent: 3, response_hours: 5.1 },
]

const severityColors: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  low: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
}

export default function IncidentPlaybookDashboard() {
  const { data: livePlaybooks } = usePlaybooks()
  const { data: liveIncidents } = useIncidents()

  const playbooks = (livePlaybooks as PlaybookDisplay[] | null) || MOCK_PLAYBOOKS
  const incidents = (liveIncidents as IncidentDisplay[] | null) || MOCK_INCIDENTS
  const totalNotifications = incidents.reduce((sum, i) => sum + i.notifications_sent, 0)
  const avgResponse = (incidents.reduce((sum, i) => sum + i.response_hours, 0) / incidents.length).toFixed(1)

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
          <p className="mt-2 text-3xl font-bold text-red-600">{incidents.length}</p>
          <p className="mt-1 text-sm text-red-500">In progress</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Avg Response</p>
            <FileCheck className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">{avgResponse}h</p>
          <p className="mt-1 text-sm text-gray-500">Mean time to respond</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Notifications Sent</p>
            <Bell className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{totalNotifications}</p>
          <p className="mt-1 text-sm text-gray-500">Active notifications</p>
        </div>
      </div>

      {/* Active Incidents */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Siren className="h-5 w-5 text-red-500" />
          <h2 className="text-lg font-semibold text-gray-900">Active Incidents</h2>
        </div>
        <div className="space-y-3">
          {incidents.map(inc => {
            const colors = severityColors[inc.severity] || severityColors.medium
            return (
              <div key={inc.id} className={`p-4 rounded-lg border ${colors.border} ${colors.bg}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${colors.text} bg-white`}>{inc.severity}</span>
                    <span className="font-medium text-gray-900">{inc.title}</span>
                  </div>
                  <span className="text-sm text-gray-500">{inc.response_hours}h elapsed</span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>Playbook: {inc.playbook}</span>
                  <span>{inc.notifications_sent} notifications sent</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Playbooks */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <FileCheck className="h-5 w-5 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-900">Playbooks</h2>
        </div>
        <div className="space-y-3">
          {playbooks.map(pb => (
            <div key={pb.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900">{pb.name}</span>
                <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700">{pb.jurisdiction}</span>
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>Deadline: {pb.notification_deadline_hours}h</span>
                <span>{pb.steps.length} steps</span>
                <span>Updated: {new Date(pb.last_updated).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
