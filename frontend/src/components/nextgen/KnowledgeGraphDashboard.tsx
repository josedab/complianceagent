'use client'

import { Network, Database, BookOpen, Layers } from 'lucide-react'
import { useKnowledgeGraphNodeTypes } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function KnowledgeGraphDashboard() {
  const { data: nodeTypes, loading, error, refetch } = useKnowledgeGraphNodeTypes()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Knowledge Graph</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{[...Array(3)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Knowledge Graph</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Knowledge Graph: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const summary = nodeTypes as Record<string, unknown> | null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Knowledge Graph</h1>
        <p className="text-gray-500">Explore relationships between regulations, controls, and assets</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard icon={<Network className="w-5 h-5 text-blue-500" />} title="Node Types" value={String(Array.isArray(summary?.node_types) ? summary.node_types.length : 0)} subtitle="Entity categories" />
        <StatCard icon={<Database className="w-5 h-5 text-green-500" />} title="Total Nodes" value={String(summary?.total_nodes ?? 0)} subtitle="Graph entities" />
        <StatCard icon={<Layers className="w-5 h-5 text-purple-500" />} title="Relationships" value={String(summary?.total_edges ?? 0)} subtitle="Graph edges" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Node Types</h2>
        {!summary || !Array.isArray(summary.node_types) || (summary.node_types as unknown[]).length === 0 ? (
          <p className="text-gray-500">No knowledge graph data yet.</p>
        ) : (
          <div className="space-y-3">
            {(summary.node_types as string[]).map((nodeType) => (
              <div key={nodeType} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <BookOpen className="w-5 h-5 text-blue-500" />
                  <p className="font-medium text-gray-900">{nodeType}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
