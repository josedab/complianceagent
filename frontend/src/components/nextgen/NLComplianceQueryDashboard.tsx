'use client'

import { Search, Brain, Database, Zap } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Show GDPR violations', detail: 'Natural language to SQL', value: 'Resolved' },
  { id: 2, name: 'List expiring controls', detail: 'Temporal query parsing', value: 'Resolved' },
  { id: 3, name: 'Compare SOC 2 gaps', detail: 'Cross-framework analysis', value: 'Resolved' },
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

export default function NLComplianceQueryDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Natural Language Query</h1>
        <p className="text-gray-500">Query compliance data using natural language</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Search className="h-5 w-5 text-blue-600" />} title="Queries" value="2.8K" subtitle="This month" />
        <StatCard icon={<Brain className="h-5 w-5 text-green-600" />} title="Accuracy" value="93%" subtitle="Query accuracy" />
        <StatCard icon={<Database className="h-5 w-5 text-purple-600" />} title="Avg Time" value="1.4s" subtitle="Response time" />
        <StatCard icon={<Zap className="h-5 w-5 text-orange-600" />} title="Sources" value="48" subtitle="Data sources" />
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
