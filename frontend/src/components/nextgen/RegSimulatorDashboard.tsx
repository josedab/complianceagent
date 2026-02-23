'use client'

import { Play, Globe, BarChart3, AlertTriangle } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'GDPR Expansion', detail: 'New sector requirements', value: '92% impact' },
  { id: 2, name: 'AI Regulation Wave', detail: 'Multi-jurisdiction analysis', value: '87% ready' },
  { id: 3, name: 'Data Sovereignty', detail: 'Cross-border restrictions', value: '78% prepared' },
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

export default function RegSimulatorDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Simulator</h1>
        <p className="text-gray-500">Simulate regulatory scenarios and compliance impact</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Play className="h-5 w-5 text-blue-600" />} title="Simulations" value="86" subtitle="Completed" />
        <StatCard icon={<Globe className="h-5 w-5 text-green-600" />} title="Scenarios" value="234" subtitle="Tested" />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-purple-600" />} title="Accuracy" value="91%" subtitle="Prediction rate" />
        <StatCard icon={<AlertTriangle className="h-5 w-5 text-orange-600" />} title="Time Saved" value="420h" subtitle="This quarter" />
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
