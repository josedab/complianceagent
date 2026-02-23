'use client'

import { Zap, GitPullRequest, Shield, Activity } from 'lucide-react'

const MOCK_DATA = [
  { id: 1, name: 'Schema drift in payments-api', status: 'healed', timestamp: '2 min ago', detail: 'Auto-reverted migration' },
  { id: 2, name: 'Broken RBAC rule in auth-service', status: 'auto-merged', timestamp: '8 min ago', detail: 'PR #412 merged' },
  { id: 3, name: 'Expired TLS cert on staging', status: 'healed', timestamp: '15 min ago', detail: 'Cert renewed automatically' },
  { id: 4, name: 'SOC2 control gap in logging', status: 'escalated', timestamp: '32 min ago', detail: 'Requires manual review' },
  { id: 5, name: 'Dependency CVE in user-service', status: 'healed', timestamp: '1 hr ago', detail: 'Patched to safe version' },
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

export default function AutoHealingDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Auto-Healing Compliance Pipeline</h1>
        <p className="text-gray-500">Self-repairing compliance workflows that detect, diagnose, and fix issues automatically</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Zap className="h-5 w-5 text-blue-600" />} title="Healed" value="23" subtitle="Issues auto-resolved this week" />
        <StatCard icon={<GitPullRequest className="h-5 w-5 text-green-600" />} title="Auto-Merged" value="14" subtitle="PRs merged without intervention" />
        <StatCard icon={<Shield className="h-5 w-5 text-purple-600" />} title="Escalated" value="3" subtitle="Required manual review" />
        <StatCard icon={<Activity className="h-5 w-5 text-orange-600" />} title="Avg Time" value="4.2m" subtitle="Mean time to remediation" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Healing Events</h2>
        <div className="space-y-3">
          {MOCK_DATA.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail} — {item.timestamp}</p>
              </div>
              <span className="text-sm text-gray-600">{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
