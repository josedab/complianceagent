'use client'

import { Globe, Lock, Network, Shield } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Threat Intelligence', detail: 'Cross-org threat sharing', value: 'Active' },
  { id: 2, name: 'Control Benchmarks', detail: 'Anonymous benchmarking', value: 'Active' },
  { id: 3, name: 'Incident Patterns', detail: 'Federated learning model', value: 'Training' },
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

export default function FederatedIntelDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Federated Compliance Intelligence</h1>
        <p className="text-gray-500">Privacy-preserving compliance intelligence sharing</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Globe className="h-5 w-5 text-blue-600" />} title="Federations" value="8" subtitle="Active" />
        <StatCard icon={<Lock className="h-5 w-5 text-green-600" />} title="Insights" value="2.4K" subtitle="Shared securely" />
        <StatCard icon={<Network className="h-5 w-5 text-purple-600" />} title="Privacy Score" value="99%" subtitle="Data protection" />
        <StatCard icon={<Shield className="h-5 w-5 text-orange-600" />} title="Partners" value="32" subtitle="Organizations" />
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
