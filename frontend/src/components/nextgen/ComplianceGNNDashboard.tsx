'use client'

import { Network, Brain, Cpu, Activity } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Control Dependencies', detail: '248 relationships mapped', value: '97%' },
  { id: 2, name: 'Risk Propagation', detail: 'Cross-domain analysis', value: '94%' },
  { id: 3, name: 'Regulation Clusters', detail: '12 clusters identified', value: '91%' },
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

export default function ComplianceGNNDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Graph Neural Network</h1>
        <p className="text-gray-500">Graph neural network for compliance relationship analysis</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Network className="h-5 w-5 text-blue-600" />} title="Nodes" value="1.2K" subtitle="In graph" />
        <StatCard icon={<Brain className="h-5 w-5 text-green-600" />} title="Edges" value="4.8K" subtitle="Relationships" />
        <StatCard icon={<Cpu className="h-5 w-5 text-purple-600" />} title="Accuracy" value="97%" subtitle="Model accuracy" />
        <StatCard icon={<Activity className="h-5 w-5 text-orange-600" />} title="Inference" value="45ms" subtitle="Avg latency" />
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
