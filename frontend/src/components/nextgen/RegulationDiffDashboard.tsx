'use client'

import { GitCompare, FileText, AlertTriangle, Calendar } from 'lucide-react'
import { useRegulationVersions, useRegulationDiffs } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function RegulationDiffDashboard() {
  const { data: versions, loading: versLoading, error: versError, refetch } = useRegulationVersions()
  const { data: diffs, loading: diffLoading, error: diffError } = useRegulationDiffs()

  const loading = versLoading || diffLoading
  const error = versError || diffError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Regulation Diff</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Regulation Diff</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Regulation Diff: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulation Diff</h1>
        <p className="text-gray-500">Track and compare regulatory requirement changes over time</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FileText className="w-5 h-5 text-blue-500" />} title="Versions" value={String(versions?.length ?? 0)} subtitle="Regulation versions" />
        <StatCard icon={<GitCompare className="w-5 h-5 text-green-500" />} title="Diffs" value={String(diffs?.length ?? 0)} subtitle="Compared diffs" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-orange-500" />} title="Critical Changes" value={String(diffs?.reduce((s, d) => s + d.critical_changes, 0) ?? 0)} subtitle="Across all diffs" />
        <StatCard icon={<Calendar className="w-5 h-5 text-purple-500" />} title="Regulations" value={String(versions ? new Set(versions.map(v => v.regulation)).size : 0)} subtitle="Unique regulations" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Regulation Versions</h2>
          {!versions || versions.length === 0 ? (
            <p className="text-gray-500">No regulation versions yet.</p>
          ) : (
            <div className="space-y-3">
              {versions.slice(0, 5).map((v) => (
                <div key={v.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{v.regulation} v{v.version}</p>
                    <p className="text-sm text-gray-500">Effective: {v.effective_date} · {v.total_articles} articles</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Diffs</h2>
          {!diffs || diffs.length === 0 ? (
            <p className="text-gray-500">No diffs computed yet.</p>
          ) : (
            <div className="space-y-3">
              {diffs.slice(0, 5).map((d) => (
                <div key={d.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{d.regulation}</p>
                    <p className="text-sm text-gray-500">v{d.from_version} → v{d.to_version} · {d.total_changes} changes</p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${d.critical_changes > 0 ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                    {d.critical_changes > 0 ? `${d.critical_changes} critical` : 'No critical'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
