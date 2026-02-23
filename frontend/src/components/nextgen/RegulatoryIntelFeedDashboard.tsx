'use client'

import { Globe, Search, Bell, Brain } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'EU Regulatory Update', detail: 'Digital Markets Act enforcement', value: 'High' },
  { id: 2, name: 'US State Privacy Laws', detail: '5 new states with bills', value: 'Medium' },
  { id: 3, name: 'APAC Data Protection', detail: 'Singapore PDPA amendments', value: 'High' },
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

export default function RegulatoryIntelFeedDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Intelligence Feed</h1>
        <p className="text-gray-500">Curated regulatory intelligence and analysis feed</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Globe className="h-5 w-5 text-blue-600" />} title="Sources" value="156" subtitle="Monitored" />
        <StatCard icon={<Search className="h-5 w-5 text-green-600" />} title="Articles" value="2.4K" subtitle="This month" />
        <StatCard icon={<Bell className="h-5 w-5 text-purple-600" />} title="Alerts" value="48" subtitle="Active" />
        <StatCard icon={<Brain className="h-5 w-5 text-orange-600" />} title="Relevance" value="94%" subtitle="AI-curated" />
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
