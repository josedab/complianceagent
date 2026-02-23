'use client'

import { Play, Shield, BarChart3, Clock } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'New Privacy Law Impact', detail: 'Assess compliance readiness', value: '94%' },
  { id: 2, name: 'Cross-Border Transfer', detail: 'Data flow restriction sim', value: '89%' },
  { id: 3, name: 'AI Act Compliance', detail: 'Algorithm audit requirements', value: '91%' },
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

export default function RegulatorySimulationDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Simulation</h1>
        <p className="text-gray-500">Run compliance simulations for regulatory changes</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Play className="h-5 w-5 text-blue-600" />} title="Simulations" value="124" subtitle="Run" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Scenarios" value="456" subtitle="Tested" />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-purple-600" />} title="Accuracy" value="93%" subtitle="Prediction accuracy" />
        <StatCard icon={<Clock className="h-5 w-5 text-orange-600" />} title="Avg Runtime" value="12m" subtitle="Per simulation" />
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
