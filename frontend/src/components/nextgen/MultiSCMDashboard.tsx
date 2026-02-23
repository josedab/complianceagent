'use client'

import { GitBranch, Globe, Code, Plug } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'GitHub Enterprise', detail: '186 repositories connected', value: 'Active' },
  { id: 2, name: 'GitLab Cloud', detail: '98 repositories monitored', value: 'Active' },
  { id: 3, name: 'Bitbucket', detail: '58 repositories tracked', value: 'Active' },
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

export default function MultiSCMDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Multi-SCM Support</h1>
        <p className="text-gray-500">Compliance across multiple source control platforms</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<GitBranch className="h-5 w-5 text-blue-600" />} title="Platforms" value="4" subtitle="Connected" />
        <StatCard icon={<Globe className="h-5 w-5 text-green-600" />} title="Repos" value="342" subtitle="Monitored" />
        <StatCard icon={<Code className="h-5 w-5 text-purple-600" />} title="Scans" value="8.5K" subtitle="This month" />
        <StatCard icon={<Plug className="h-5 w-5 text-orange-600" />} title="Findings" value="567" subtitle="Total active" />
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
