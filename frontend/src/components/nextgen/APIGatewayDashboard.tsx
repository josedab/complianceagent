'use client'

import { Key, Globe, BarChart3, Shield } from 'lucide-react'

const MOCK_CLIENTS = [
  { id: 1, name: 'ComplianceBot Pro', tier: 'Enterprise', requests: '1.2M', latency: '45ms', errorRate: '0.02%', status: 'Active' },
  { id: 2, name: 'AuditFlow SDK', tier: 'Professional', requests: '850K', latency: '62ms', errorRate: '0.05%', status: 'Active' },
  { id: 3, name: 'RegWatch Scanner', tier: 'Enterprise', requests: '2.1M', latency: '38ms', errorRate: '0.01%', status: 'Active' },
  { id: 4, name: 'PolicyCheck API', tier: 'Starter', requests: '120K', latency: '95ms', errorRate: '0.12%', status: 'Rate Limited' },
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

export default function APIGatewayDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">API Gateway</h1>
        <p className="text-gray-500">Manage OAuth clients, rate limiting, and API traffic</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Key className="w-5 h-5 text-blue-500" />} title="OAuth Clients" value="4" subtitle="3 enterprise + starter" />
        <StatCard icon={<Globe className="w-5 h-5 text-green-500" />} title="Total Requests" value="4.27M" subtitle="Last 30 days" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-purple-500" />} title="Avg Latency" value="60ms" subtitle="p95 across all clients" />
        <StatCard icon={<Shield className="w-5 h-5 text-orange-500" />} title="Error Rate" value="0.05%" subtitle="Below 0.1% threshold" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">OAuth Clients</h2>
        <div className="space-y-3">
          {MOCK_CLIENTS.map((client) => (
            <div key={client.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Key className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="font-medium text-gray-900">{client.name}</p>
                  <p className="text-sm text-gray-500">{client.requests} requests · {client.latency} latency · {client.errorRate} errors</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  client.tier === 'Enterprise' ? 'bg-purple-100 text-purple-700' :
                  client.tier === 'Professional' ? 'bg-blue-100 text-blue-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {client.tier}
                </span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  client.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {client.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
