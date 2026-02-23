'use client'

import { Zap, GitPullRequest, Shield, Clock } from 'lucide-react'

const MOCK_DATA = [
  { id: 1, name: 'HIPAA encryption remediation', status: 'active', prsCreated: 3, mergeRate: '100%' },
  { id: 2, name: 'SOC2 logging gaps pipeline', status: 'active', prsCreated: 7, mergeRate: '86%' },
  { id: 3, name: 'PCI-DSS access control fixes', status: 'completed', prsCreated: 5, mergeRate: '100%' },
  { id: 4, name: 'GDPR data retention cleanup', status: 'pending', prsCreated: 0, mergeRate: '—' },
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

export default function AutoRemediationDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Auto-Remediation</h1>
        <p className="text-gray-500">Automated pipelines that generate, test, and merge compliance fixes</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Zap className="h-5 w-5 text-blue-600" />} title="Pipelines" value="4" subtitle="Active remediation pipelines" />
        <StatCard icon={<GitPullRequest className="h-5 w-5 text-green-600" />} title="PRs Created" value="15" subtitle="Pull requests generated" />
        <StatCard icon={<Shield className="h-5 w-5 text-purple-600" />} title="Auto-Merge Rate" value="93%" subtitle="PRs merged without manual review" />
        <StatCard icon={<Clock className="h-5 w-5 text-orange-600" />} title="Avg Fix Time" value="12m" subtitle="Mean time from detection to fix" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Remediation Pipelines</h2>
        <div className="space-y-3">
          {MOCK_DATA.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.prsCreated} PRs created · Merge rate: {item.mergeRate}</p>
              </div>
              <span className="text-sm text-gray-600">{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
