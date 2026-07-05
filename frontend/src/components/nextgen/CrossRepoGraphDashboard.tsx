'use client'

import { GitBranch, Network, AlertTriangle, CheckCircle } from 'lucide-react'
import { useCrossRepoGraph } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function CrossRepoGraphDashboard() {
  const { data: graph, loading, error, refetch } = useCrossRepoGraph()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Cross-Repo Graph</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Cross-Repo Graph</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Cross-Repo Graph: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const nodes = graph?.nodes ?? []
  const edges = graph?.edges ?? []
  const hotspots = graph?.hotspots ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cross-Repository Compliance Graph</h1>
        <p className="text-gray-500">Visualize compliance dependencies and hotspots across repositories</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<GitBranch className="w-5 h-5 text-blue-500" />} title="Repositories" value={String(nodes.length)} subtitle="Graph nodes" />
        <StatCard icon={<Network className="w-5 h-5 text-green-500" />} title="Dependencies" value={String(edges.length)} subtitle="Graph edges" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-orange-500" />} title="Hotspots" value={String(hotspots.length)} subtitle="Risk hotspots" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-purple-500" />} title="Overall Score" value={`${(graph?.overall_score ?? 0).toFixed(1)}%`} subtitle="Graph compliance" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Repository Nodes</h2>
        {nodes.length === 0 ? (
          <p className="text-gray-500">No repository graph data yet.</p>
        ) : (
          <div className="space-y-3">
            {nodes.slice(0, 10).map((node) => (
              <div key={node.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <GitBranch className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{node.full_name}</p>
                    <p className="text-sm text-gray-500">Grade: {node.grade} · Violations: {node.violations} · Frameworks: {node.frameworks.join(', ')}</p>
                  </div>
                </div>
                <span className="text-sm font-medium text-gray-700">{node.score.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
