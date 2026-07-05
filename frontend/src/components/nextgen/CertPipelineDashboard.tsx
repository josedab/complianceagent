'use client'

import { Shield, CheckCircle, AlertCircle, BarChart3 } from 'lucide-react'
import { useCertRuns, useCertPipelineStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function CertPipelineDashboard() {
  const { data: runs, loading: runsLoading, error: runsError, refetch } = useCertRuns()
  const { data: stats, loading: statsLoading, error: statsError } = useCertPipelineStats()

  const loading = runsLoading || statsLoading
  const error = runsError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Certification Pipeline</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Certification Pipeline</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Cert Pipeline: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Certification Pipeline</h1>
        <p className="text-gray-500">Automated evidence collection and certification pipeline management</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Shield className="w-5 h-5 text-blue-500" />} title="Total Runs" value={String(stats?.total_runs ?? 0)} subtitle={`${stats?.completed_runs ?? 0} completed`} />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-500" />} title="In Progress" value={String(stats?.in_progress_runs ?? 0)} subtitle="Active runs" />
        <StatCard icon={<AlertCircle className="w-5 h-5 text-orange-500" />} title="Open Gaps" value={String((stats?.total_gaps ?? 0) - (stats?.resolved_gaps ?? 0))} subtitle={`${stats?.resolved_gaps ?? 0} resolved`} />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-purple-500" />} title="Avg Completion" value={`${(stats?.avg_completion_days ?? 0).toFixed(1)}d`} subtitle="Days to complete" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Certification Runs</h2>
        {!runs || runs.length === 0 ? (
          <p className="text-gray-500">No certification runs yet.</p>
        ) : (
          <div className="space-y-3">
            {runs.map((run) => (
              <div key={run.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Shield className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{run.repo}</p>
                    <p className="text-sm text-gray-500">{run.framework} · Stage: {run.stage} · {run.progress_pct.toFixed(1)}%</p>
                  </div>
                </div>
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${run.progress_pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
