'use client'

import { FileCode, AlertTriangle, CheckCircle, Clock } from 'lucide-react'

const MOCK_DATA = [
  { id: 1, name: 'PR #412 — Add payment endpoint', detail: '3 compliance findings, 1 critical (PCI scope)', status: 'Needs Review' },
  { id: 2, name: 'PR #408 — Update auth middleware', detail: '0 findings — all checks passed', status: 'Approved' },
  { id: 3, name: 'PR #405 — Data export feature', detail: '2 findings — GDPR data-residency warning', status: 'Changes Requested' },
  { id: 4, name: 'PR #401 — Logging refactor', detail: '1 finding — PII leak in debug logs', status: 'In Progress' },
]

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm text-gray-500">{title}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function CodeReviewAgentDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance-Aware Code Review Agent</h1>
        <p className="text-gray-500">AI-powered pull request reviews with compliance violation detection</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FileCode className="h-5 w-5 text-blue-600" />} title="PRs Reviewed" value="48" subtitle="This sprint" />
        <StatCard icon={<AlertTriangle className="h-5 w-5 text-green-600" />} title="Findings" value="12" subtitle="Compliance issues found" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-purple-600" />} title="Pass Rate" value="75%" subtitle="Clean first-pass reviews" />
        <StatCard icon={<Clock className="h-5 w-5 text-orange-600" />} title="Avg Review Time" value="2.4m" subtitle="Per pull request" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent PR Reviews</h2>
        <div className="space-y-3">
          {MOCK_DATA.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail}</p>
              </div>
              <span className="text-sm text-gray-600">{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
