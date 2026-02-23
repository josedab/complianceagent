'use client'

import { GitBranch, Code, Shield, Activity } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'PR Compliance Check', detail: 'Auto-check on pull requests', value: 'Active' },
  { id: 2, name: 'Branch Protection', detail: 'Enforce compliance rules', value: 'Active' },
  { id: 3, name: 'Secret Scanner', detail: 'Detect exposed credentials', value: 'Active' },
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

export default function GitHubAppDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">GitHub App</h1>
        <p className="text-gray-500">GitHub App integration for compliance workflows</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<GitBranch className="h-5 w-5 text-blue-600" />} title="Repos" value="86" subtitle="Connected" />
        <StatCard icon={<Code className="h-5 w-5 text-green-600" />} title="Scans" value="1.4K" subtitle="This month" />
        <StatCard icon={<Shield className="h-5 w-5 text-purple-600" />} title="Issues Found" value="234" subtitle="Total" />
        <StatCard icon={<Activity className="h-5 w-5 text-orange-600" />} title="Auto-Fixed" value="189" subtitle="Automatically" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Items</h2>
        <div className="space-y-3">
          {ITEMS.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail}</p>
              </div>
              <span className="text-sm text-gray-600">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
