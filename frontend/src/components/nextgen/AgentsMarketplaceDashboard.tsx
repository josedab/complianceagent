'use client'

import { Package, Download, Star, BarChart3 } from 'lucide-react'
import { useMarketplaceAgents, useAgentsMarketplaceStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function AgentsMarketplaceDashboard() {
  const { data: agents, loading: agentsLoading, error: agentsError, refetch } = useMarketplaceAgents()
  const { data: stats, loading: statsLoading, error: statsError } = useAgentsMarketplaceStats()

  const loading = agentsLoading || statsLoading
  const error = agentsError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Agents Marketplace</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-64 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Agents Marketplace</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Agents Marketplace: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Agents Marketplace</h1>
        <p className="text-gray-500">Discover and install compliance agents for your workflows</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Package className="w-5 h-5 text-blue-500" />} title="Total Agents" value={String(stats?.total_agents ?? 0)} subtitle={`${stats?.published_agents ?? 0} published`} />
        <StatCard icon={<Download className="w-5 h-5 text-green-500" />} title="Installations" value={String(stats?.total_installations ?? 0)} subtitle="All time installs" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-purple-500" />} title="Executions" value={String(stats?.total_executions ?? 0)} subtitle="Total executions" />
        <StatCard icon={<Star className="w-5 h-5 text-orange-500" />} title="Categories" value={String(Object.keys(stats?.by_category ?? {}).length)} subtitle="Agent categories" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Available Agents</h2>
        {!agents || agents.length === 0 ? (
          <p className="text-gray-500">No agents in marketplace yet.</p>
        ) : (
          <div className="space-y-3">
            {agents.map((agent) => (
              <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Package className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{agent.name}</p>
                    <p className="text-sm text-gray-500">{agent.author} · {agent.downloads} downloads · ⭐ {agent.rating.toFixed(1)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">{agent.category}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${agent.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>{agent.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
