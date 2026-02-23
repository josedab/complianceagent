'use client'

import { Database, TrendingUp, Clock, Layers } from 'lucide-react'

const MOCK_EVENT_TYPES = [
  { id: 1, name: 'Access Log Events', tenant: 'Acme Corp', volume: '2.4M', lastIngested: '2 min ago', status: 'Active' },
  { id: 2, name: 'Policy Change Events', tenant: 'GlobalBank', volume: '890K', lastIngested: '5 min ago', status: 'Active' },
  { id: 3, name: 'Audit Trail Events', tenant: 'HealthFirst', volume: '1.7M', lastIngested: '12 min ago', status: 'Active' },
  { id: 4, name: 'Incident Response Events', tenant: 'TechVault', volume: '340K', lastIngested: '1 hr ago', status: 'Paused' },
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

export default function ComplianceDataLakeDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Multi-Tenant Compliance Data Lake</h1>
        <p className="text-gray-500">Centralized compliance event ingestion and storage across tenants</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Database className="w-5 h-5 text-blue-500" />} title="Total Records" value="5.3M" subtitle="Across all tenants" />
        <StatCard icon={<TrendingUp className="w-5 h-5 text-green-500" />} title="Ingestion Rate" value="12K/min" subtitle="Current throughput" />
        <StatCard icon={<Clock className="w-5 h-5 text-yellow-500" />} title="Avg Latency" value="230ms" subtitle="End-to-end pipeline" />
        <StatCard icon={<Layers className="w-5 h-5 text-purple-500" />} title="Active Tenants" value="4" subtitle="With active streams" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Event Types</h2>
        <div className="space-y-3">
          {MOCK_EVENT_TYPES.map((evt) => (
            <div key={evt.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Layers className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="font-medium text-gray-900">{evt.name}</p>
                  <p className="text-sm text-gray-500">{evt.tenant} · {evt.volume} records · Last ingested {evt.lastIngested}</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                evt.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
              }`}>
                {evt.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
