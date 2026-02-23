'use client'

import { Network, Shield, Globe, Lock } from 'lucide-react'

const MOCK_NODES = [
  { org: 'Acme Corp', role: 'participant', insights: 42, status: 'active' },
  { org: 'FinServ Inc', role: 'participant', insights: 38, status: 'active' },
  { org: 'HealthFirst', role: 'coordinator', insights: 67, status: 'active' },
  { org: 'TechCo', role: 'observer', insights: 12, status: 'pending' },
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

export default function DataMeshFederationDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Data Mesh Federation</h1>
        <p className="text-gray-500">Federated compliance data sharing with zero-knowledge proofs</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Network className="h-5 w-5 text-blue-600" />} title="Nodes" value={String(MOCK_NODES.length)} subtitle="Federation members" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Insights" value="159" subtitle="Shared securely" />
        <StatCard icon={<Lock className="h-5 w-5 text-purple-600" />} title="Proofs" value="312" subtitle="Verified" />
        <StatCard icon={<Globe className="h-5 w-5 text-orange-600" />} title="Status" value="Active" subtitle="Network healthy" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Federation Nodes</h2>
        <div className="space-y-3">
          {MOCK_NODES.map((node) => (
            <div key={node.org} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{node.org}</span>
                <p className="text-xs text-gray-500">{node.role} · {node.insights} insights</p>
              </div>
              <span className={`px-2 py-0.5 text-xs rounded ${node.status === 'active' ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700'}`}>{node.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
