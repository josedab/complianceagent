'use client'

import { Brain, TrendingUp, Globe, AlertTriangle } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'EU AI Act Enforcement', detail: 'Expected implementation Q3', value: 'High' },
  { id: 2, name: 'US Privacy Law', detail: 'Federal bill probability', value: 'Medium' },
  { id: 3, name: 'APAC Data Rules', detail: 'Cross-border changes', value: 'High' },
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

export default function PredictionsDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Predictions</h1>
        <p className="text-gray-500">AI-powered regulatory change predictions</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Brain className="h-5 w-5 text-blue-600" />} title="Predictions" value="48" subtitle="Active" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-green-600" />} title="Accuracy" value="89%" subtitle="Historical accuracy" />
        <StatCard icon={<Globe className="h-5 w-5 text-purple-600" />} title="Regions" value="12" subtitle="Monitored" />
        <StatCard icon={<AlertTriangle className="h-5 w-5 text-orange-600" />} title="Upcoming" value="8" subtitle="Changes expected" />
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
