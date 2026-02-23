'use client'

import { Cpu, Layers, Activity, Monitor } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Production Mirror', detail: 'Live environment replica', value: '99% sync' },
  { id: 2, name: 'Pre-Deployment Test', detail: 'Change impact simulation', value: '96% accurate' },
  { id: 3, name: 'Disaster Recovery', detail: 'DR scenario modeling', value: '94% coverage' },
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

export default function TwinSimulationDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Digital Twin Simulation</h1>
        <p className="text-gray-500">Digital twin for compliance environment simulation</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Cpu className="h-5 w-5 text-blue-600" />} title="Twins" value="8" subtitle="Active" />
        <StatCard icon={<Layers className="h-5 w-5 text-green-600" />} title="Simulations" value="456" subtitle="Run" />
        <StatCard icon={<Activity className="h-5 w-5 text-purple-600" />} title="Accuracy" value="96%" subtitle="Model fidelity" />
        <StatCard icon={<Monitor className="h-5 w-5 text-orange-600" />} title="Scenarios" value="24" subtitle="Tested" />
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
