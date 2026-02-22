'use client'

import { useState } from 'react'
import { Users, Shield, Clock, FileCheck, AlertCircle, CheckCircle2 } from 'lucide-react'

interface AuditorSession {
  id: string
  auditor_email: string
  firm: string
  framework: string
  status: 'active' | 'expired' | 'revoked'
  created_at: string
  expires_at: string
}

interface ReadinessReport {
  framework: string
  total_controls: number
  covered_controls: number
  coverage_percentage: number
  readiness_score: 'ready' | 'needs_work' | 'not_ready'
  gaps: { control: string; control_name: string; status: string }[]
}

const MOCK_SESSIONS: AuditorSession[] = [
  { id: 'sess-1', auditor_email: 'auditor@deloitte.com', firm: 'Deloitte', framework: 'soc2', status: 'active', created_at: '2026-02-18T10:00:00Z', expires_at: '2026-02-21T10:00:00Z' },
  { id: 'sess-2', auditor_email: 'reviewer@kpmg.com', firm: 'KPMG', framework: 'iso27001', status: 'expired', created_at: '2026-02-10T09:00:00Z', expires_at: '2026-02-13T09:00:00Z' },
]

const MOCK_REPORTS: ReadinessReport[] = [
  { framework: 'SOC 2 Type II', total_controls: 61, covered_controls: 48, coverage_percentage: 78.7, readiness_score: 'needs_work', gaps: [{ control: 'CC6.3', control_name: 'Access Provisioning', status: 'missing_evidence' }, { control: 'CC7.2', control_name: 'Monitoring Activities', status: 'missing_evidence' }] },
  { framework: 'ISO 27001', total_controls: 93, covered_controls: 81, coverage_percentage: 87.1, readiness_score: 'ready', gaps: [{ control: 'A.12.4', control_name: 'Logging and Monitoring', status: 'missing_evidence' }] },
  { framework: 'HIPAA', total_controls: 42, covered_controls: 29, coverage_percentage: 69.0, readiness_score: 'needs_work', gaps: [{ control: '164.312(a)', control_name: 'Access Control', status: 'missing_evidence' }, { control: '164.312(e)', control_name: 'Transmission Security', status: 'missing_evidence' }] },
]

export default function AuditorPortalDashboard() {
  const [activeTab, setActiveTab] = useState<'sessions' | 'readiness'>('readiness')

  const readinessColor = (score: string) => {
    if (score === 'ready') return 'text-green-600 bg-green-50'
    if (score === 'needs_work') return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Auditor Portal</h1>
        <p className="text-gray-500 mt-1">Manage auditor sessions and audit readiness across frameworks</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><Users className="w-4 h-4" /> Active Sessions</div>
          <div className="text-2xl font-bold">{MOCK_SESSIONS.filter(s => s.status === 'active').length}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><Shield className="w-4 h-4" /> Frameworks Tracked</div>
          <div className="text-2xl font-bold">{MOCK_REPORTS.length}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><CheckCircle2 className="w-4 h-4" /> Audit-Ready</div>
          <div className="text-2xl font-bold">{MOCK_REPORTS.filter(r => r.readiness_score === 'ready').length}/{MOCK_REPORTS.length}</div>
        </div>
      </div>

      <div className="flex gap-4 border-b">
        <button onClick={() => setActiveTab('readiness')} className={`pb-2 px-1 text-sm font-medium ${activeTab === 'readiness' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}>
          <FileCheck className="w-4 h-4 inline mr-1" /> Readiness Reports
        </button>
        <button onClick={() => setActiveTab('sessions')} className={`pb-2 px-1 text-sm font-medium ${activeTab === 'sessions' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}>
          <Users className="w-4 h-4 inline mr-1" /> Auditor Sessions
        </button>
      </div>

      {activeTab === 'readiness' && (
        <div className="space-y-4">
          {MOCK_REPORTS.map(report => (
            <div key={report.framework} className="bg-white dark:bg-gray-800 rounded-lg border p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-medium text-lg">{report.framework}</h3>
                  <p className="text-sm text-gray-500">{report.covered_controls}/{report.total_controls} controls covered</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${readinessColor(report.readiness_score)}`}>
                  {report.readiness_score.replace('_', ' ')}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                <div className={`h-2 rounded-full ${report.coverage_percentage >= 80 ? 'bg-green-500' : report.coverage_percentage >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${report.coverage_percentage}%` }} />
              </div>
              {report.gaps.length > 0 && (
                <div className="mt-2">
                  <p className="text-sm font-medium text-gray-600 mb-1"><AlertCircle className="w-3 h-3 inline mr-1" />{report.gaps.length} gap(s):</p>
                  <ul className="text-sm text-gray-500 space-y-1">
                    {report.gaps.map(gap => (
                      <li key={gap.control}>• {gap.control} — {gap.control_name}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'sessions' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border">
          <table className="w-full">
            <thead>
              <tr className="border-b text-left text-sm text-gray-500">
                <th className="p-3">Auditor</th>
                <th className="p-3">Firm</th>
                <th className="p-3">Framework</th>
                <th className="p-3">Status</th>
                <th className="p-3">Expires</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_SESSIONS.map(session => (
                <tr key={session.id} className="border-b last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="p-3">{session.auditor_email}</td>
                  <td className="p-3">{session.firm}</td>
                  <td className="p-3 uppercase text-sm font-medium">{session.framework}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${session.status === 'active' ? 'bg-green-100 text-green-700' : session.status === 'expired' ? 'bg-gray-100 text-gray-600' : 'bg-red-100 text-red-700'}`}>
                      {session.status}
                    </span>
                  </td>
                  <td className="p-3 text-sm text-gray-500"><Clock className="w-3 h-3 inline mr-1" />{new Date(session.expires_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
