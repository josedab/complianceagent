'use client'

import { Plug, Package, Download, Star } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'AWS Compliance Plugin', detail: 'Cloud compliance scanner', value: '3.2K installs' },
  { id: 2, name: 'JIRA Integration', detail: 'Issue tracking connector', value: '2.8K installs' },
  { id: 3, name: 'Slack Notifier', detail: 'Real-time alerts plugin', value: '2.1K installs' },
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

export default function PluginEcosystemDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Plugin Ecosystem</h1>
        <p className="text-gray-500">Extensible plugin system for compliance tools</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Plug className="h-5 w-5 text-blue-600" />} title="Plugins" value="86" subtitle="Published" />
        <StatCard icon={<Package className="h-5 w-5 text-green-600" />} title="Installs" value="12K" subtitle="Total" />
        <StatCard icon={<Download className="h-5 w-5 text-purple-600" />} title="Developers" value="48" subtitle="Contributing" />
        <StatCard icon={<Star className="h-5 w-5 text-orange-600" />} title="Rating" value="4.6" subtitle="Avg rating" />
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
