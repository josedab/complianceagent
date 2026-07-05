'use client'

import { Building, Network, BarChart3, ChevronRight } from 'lucide-react'
import { useEntityHierarchy } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function EntityRollupDashboard() {
  const { data: entities, loading, error, refetch } = useEntityHierarchy()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Entity Rollup</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{[...Array(3)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Entity Rollup</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Entity Rollup: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const avgScore = entities && entities.length > 0
    ? entities.reduce((s, e) => s + e.compliance_score, 0) / entities.length
    : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Entity Compliance Rollup</h1>
        <p className="text-gray-500">Aggregate compliance scores across organizational entities</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard icon={<Building className="w-5 h-5 text-blue-500" />} title="Entities" value={String(entities?.length ?? 0)} subtitle="Org entities" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-green-500" />} title="Avg Score" value={`${avgScore.toFixed(1)}%`} subtitle="Compliance score" />
        <StatCard icon={<Network className="w-5 h-5 text-purple-500" />} title="Levels" value={String(entities ? new Set(entities.map(e => e.level)).size : 0)} subtitle="Hierarchy levels" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Entity Hierarchy</h2>
        {!entities || entities.length === 0 ? (
          <p className="text-gray-500">No entities found.</p>
        ) : (
          <div className="space-y-3">
            {entities.map((entity) => (
              <div key={entity.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Building className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{entity.name}</p>
                    <p className="text-sm text-gray-500">Level: {entity.level} · Members: {entity.member_count}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-700">{entity.compliance_score.toFixed(1)}%</span>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
