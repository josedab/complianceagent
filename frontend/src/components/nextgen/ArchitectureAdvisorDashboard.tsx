'use client'

import { Building2, Layers, Network, Target } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Microservices Migration', detail: 'Event-driven pattern recommended', value: '92%' },
  { id: 2, name: 'Data Layer Refactor', detail: 'CQRS pattern suggested', value: '87%' },
  { id: 3, name: 'API Gateway Setup', detail: 'Gateway pattern applied', value: '95%' },
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

export default function ArchitectureAdvisorDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Architecture Advisor</h1>
        <p className="text-gray-500">AI-powered architecture recommendations and analysis</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Building2 className="h-5 w-5 text-blue-600" />} title="Patterns" value="24" subtitle="Analyzed" />
        <StatCard icon={<Layers className="h-5 w-5 text-green-600" />} title="Components" value="156" subtitle="Mapped" />
        <StatCard icon={<Network className="h-5 w-5 text-purple-600" />} title="Score" value="94%" subtitle="Architecture health" />
        <StatCard icon={<Target className="h-5 w-5 text-orange-600" />} title="Reviews" value="12" subtitle="This month" />
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
