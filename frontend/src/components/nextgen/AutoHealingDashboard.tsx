'use client'

import { Zap, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react'
import { useAutoHealingRuns, useAutoHealingMetrics } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function AutoHealingDashboard() {
  const { data: runs, loading: runsLoading, error: runsError, refetch } = useAutoHealingRuns()
  const { data: metrics, loading: metricsLoading, error: metricsError } = useAutoHealingMetrics()

  const loading = runsLoading || metricsLoading
  const error = runsError || metricsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Auto-Healing Pipeline</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Auto-Healing Pipeline</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Auto-Healing: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Auto-Healing Pipeline</h1>
        <p className="text-gray-500">Autonomous compliance fix generation and deployment</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Zap className="w-5 h-5 text-blue-500" />} title="Total Runs" value={String(metrics?.total_runs ?? 0)} subtitle={`${metrics?.successful_runs ?? 0} successful`} />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-500" />} title="Violations Resolved" value={String(metrics?.violations_resolved ?? 0)} subtitle="Auto-healed" />
        <StatCard icon={<TrendingUp className="w-5 h-5 text-purple-500" />} title="Auto-Merge Rate" value={`${((metrics?.auto_merge_rate ?? 0) * 100).toFixed(1)}%`} subtitle="Of generated fixes" />
        <StatCard icon={<AlertCircle className="w-5 h-5 text-orange-500" />} title="Avg Fix Time" value={`${(metrics?.avg_time_to_fix_hours ?? 0).toFixed(1)}h`} subtitle="Time to resolution" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Pipeline Runs</h2>
        {!runs || runs.length === 0 ? (
          <p className="text-gray-500">No pipeline runs yet.</p>
        ) : (
          <div className="space-y-3">
            {runs.map((run) => (
              <div key={run.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Zap className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{run.repository}</p>
                    <p className="text-sm text-gray-500">{run.regulation} · {run.violations_detected} violations · {run.fixes_generated} fixes</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  run.state === 'completed' ? 'bg-green-100 text-green-700' :
                  run.state === 'running' ? 'bg-blue-100 text-blue-700' :
                  run.state === 'failed' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-700'
                }`}>{run.state}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
