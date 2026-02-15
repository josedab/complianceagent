'use client'

import { useState } from 'react'
import { AlertTriangle, Clock, FileCode, GitPullRequest, Bell, ChevronDown, ChevronUp } from 'lucide-react'

type Severity = 'critical' | 'high' | 'medium' | 'low'
type RemediationStatus = 'detected' | 'analyzing' | 'remediating' | 'pr_created' | 'awaiting_approval' | 'merged' | 'verified' | 'closed'

interface Incident {
  id: string
  title: string
  description: string
  source: string
  severity: Severity
  status: RemediationStatus
  affectedFrameworks: string[]
  affectedFiles: string[]
  cvssScore: number
  complianceImpactScore: number
  remediationPrUrl: string
  breachNotificationRequired: boolean
  detectedAt: string
}

const severityConfig: Record<Severity, { color: string; bg: string }> = {
  critical: { color: 'text-red-700', bg: 'bg-red-100' },
  high: { color: 'text-orange-700', bg: 'bg-orange-100' },
  medium: { color: 'text-yellow-700', bg: 'bg-yellow-100' },
  low: { color: 'text-blue-700', bg: 'bg-blue-100' },
}

const statusSteps: RemediationStatus[] = ['detected', 'analyzing', 'remediating', 'pr_created', 'awaiting_approval', 'merged', 'verified', 'closed']

const MOCK_INCIDENTS: Incident[] = [
  {
    id: '1', title: 'Unencrypted PII in API Response', description: 'Datadog alert: /api/users endpoint returning SSN in plaintext response body.',
    source: 'datadog', severity: 'critical', status: 'pr_created',
    affectedFrameworks: ['GDPR', 'HIPAA', 'PCI-DSS'], affectedFiles: ['src/api/users.py', 'src/models/user.py'],
    cvssScore: 8.5, complianceImpactScore: 9.2, remediationPrUrl: 'https://github.com/example/pr/142',
    breachNotificationRequired: true, detectedAt: new Date(Date.now() - 4 * 3600000).toISOString(),
  },
  {
    id: '2', title: 'Disabled Audit Logging on Payment Service', description: 'Splunk detected gap in audit logs for payment processing.',
    source: 'splunk', severity: 'high', status: 'remediating',
    affectedFrameworks: ['PCI-DSS', 'SOC 2'], affectedFiles: ['src/services/payment.py', 'config/logging.yaml'],
    cvssScore: 6.8, complianceImpactScore: 7.5, remediationPrUrl: '',
    breachNotificationRequired: false, detectedAt: new Date(Date.now() - 2 * 3600000).toISOString(),
  },
  {
    id: '3', title: 'Excessive Data Retention in Analytics DB', description: 'User behavior data older than 90-day retention policy detected.',
    source: 'elastic', severity: 'medium', status: 'detected',
    affectedFrameworks: ['GDPR'], affectedFiles: ['src/jobs/analytics_cleanup.py'],
    cvssScore: 4.2, complianceImpactScore: 5.8, remediationPrUrl: '',
    breachNotificationRequired: false, detectedAt: new Date(Date.now() - 30 * 60000).toISOString(),
  },
]

export default function IncidentRemediationDashboard() {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const hoursAgo = (iso: string) => {
    const diff = Date.now() - new Date(iso).getTime()
    const h = Math.floor(diff / 3600000)
    return h < 1 ? `${Math.floor(diff / 60000)}m ago` : `${h}h ago`
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><AlertTriangle className="h-7 w-7 text-red-600" /> Incident Auto-Remediation</h1>
        <p className="text-gray-500 mt-1">Automated incident detection → compliance mapping → remediation PR generation</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-red-50 rounded-lg border border-red-200 p-4">
          <div className="text-sm text-red-600">Critical</div>
          <div className="text-2xl font-bold text-red-700">{MOCK_INCIDENTS.filter(i => i.severity === 'critical').length}</div>
        </div>
        <div className="bg-orange-50 rounded-lg border border-orange-200 p-4">
          <div className="text-sm text-orange-600">High</div>
          <div className="text-2xl font-bold text-orange-700">{MOCK_INCIDENTS.filter(i => i.severity === 'high').length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Avg Response</div>
          <div className="text-2xl font-bold">&lt;15min</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">PRs Created</div>
          <div className="text-2xl font-bold text-green-600">1</div>
        </div>
      </div>

      {/* Incidents */}
      <div className="space-y-4">
        {MOCK_INCIDENTS.map(incident => {
          const sev = severityConfig[incident.severity]
          const expanded = expandedId === incident.id
          const currentStep = statusSteps.indexOf(incident.status)

          return (
            <div key={incident.id} className="bg-white rounded-lg border overflow-hidden">
              <div className="p-5 cursor-pointer" onClick={() => setExpandedId(expanded ? null : incident.id)}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${sev.bg} ${sev.color}`}>{incident.severity}</span>
                      <span className="text-xs text-gray-500 uppercase">{incident.source}</span>
                      {incident.breachNotificationRequired && (
                        <span className="flex items-center gap-1 text-xs text-red-600"><Bell className="h-3 w-3" /> Breach Notification Required</span>
                      )}
                    </div>
                    <h3 className="text-lg font-semibold">{incident.title}</h3>
                    <p className="text-gray-600 text-sm mt-1">{incident.description}</p>
                    <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{hoursAgo(incident.detectedAt)}</span>
                      <span>CVSS: {incident.cvssScore}</span>
                      <span>Impact: {incident.complianceImpactScore}</span>
                      {incident.affectedFrameworks.map(fw => (
                        <span key={fw} className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded">{fw}</span>
                      ))}
                    </div>
                  </div>
                  {expanded ? <ChevronUp className="h-5 w-5 text-gray-400" /> : <ChevronDown className="h-5 w-5 text-gray-400" />}
                </div>

                {/* Progress Bar */}
                <div className="mt-4 flex gap-1">
                  {statusSteps.slice(0, 5).map((step, i) => (
                    <div key={step} className="flex-1">
                      <div className={`h-1.5 rounded-full ${i <= currentStep ? 'bg-green-500' : 'bg-gray-200'}`} />
                      <div className={`text-xs mt-1 ${i <= currentStep ? 'text-green-600' : 'text-gray-400'}`}>
                        {step.replace('_', ' ')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {expanded && (
                <div className="px-5 pb-5 border-t pt-4 space-y-3">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 flex items-center gap-1"><FileCode className="h-4 w-4" /> Affected Files</h4>
                    <div className="mt-1 space-y-1">
                      {incident.affectedFiles.map(f => (
                        <code key={f} className="block text-sm bg-gray-50 px-2 py-1 rounded">{f}</code>
                      ))}
                    </div>
                  </div>
                  {incident.remediationPrUrl && (
                    <div className="flex items-center gap-2">
                      <GitPullRequest className="h-4 w-4 text-green-600" />
                      <a href={incident.remediationPrUrl} className="text-sm text-blue-600 hover:underline" target="_blank" rel="noreferrer">
                        View Remediation PR
                      </a>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <button className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">Generate Remediation</button>
                    {incident.breachNotificationRequired && (
                      <button className="px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700">Draft Breach Notice</button>
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
