'use client'

import { Database, Network, CheckCircle, Activity } from 'lucide-react'
import { useDataMeshNodes, useFederationStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function DataMeshFederationDashboard() {
  const { data: nodes, loading: nodesLoading, error: nodesError, refetch } = useDataMeshNodes()
  const { data: stats, loading: statsLoading, error: statsError } = useFederationStats()

  const loading = nodesLoading || statsLoading
  const error = nodesError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Data Mesh Federation</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Data Mesh Federation</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Data Mesh Federation: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Data Mesh Federation</h1>
        <p className="text-gray-500">Federated compliance data across domains and mesh nodes</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Network className="w-5 h-5 text-blue-500" />} title="Total Nodes" value={String(stats?.total_nodes ?? 0)} subtitle="Mesh nodes" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-500" />} title="Active Nodes" value={String(stats?.active_nodes ?? 0)} subtitle="Connected nodes" />
        <StatCard icon={<Database className="w-5 h-5 text-purple-500" />} title="Insights" value={String(stats?.total_insights ?? 0)} subtitle="Federated insights" />
        <StatCard icon={<Activity className="w-5 h-5 text-orange-500" />} title="Verified" value={String(stats?.verified_insights ?? 0)} subtitle="Verified insights" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Mesh Nodes</h2>
        {!nodes || nodes.length === 0 ? (
          <p className="text-gray-500">No mesh nodes registered yet.</p>
        ) : (
          <div className="space-y-3">
            {nodes.map((node) => (
              <div key={node.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Database className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{node.org_name}</p>
                    <p className="text-sm text-gray-500">Role: {node.role} · Joined: {node.joined_at ?? 'N/A'}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  node.status === 'active' ? 'bg-green-100 text-green-700' :
                  node.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>{node.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
