'use client'

import { Wrench, CheckCircle, GitPullRequest, TrendingUp } from 'lucide-react'
import { useAutoRemediationPipelines, useAutoRemediationStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function AutoRemediationDashboard() {
  const { data: pipelines, loading: pipelinesLoading, error: pipelinesError, refetch } = useAutoRemediationPipelines()
  const { data: stats, loading: statsLoading, error: statsError } = useAutoRemediationStats()

  const loading = pipelinesLoading || statsLoading
  const error = pipelinesError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Auto Remediation</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Auto Remediation</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Auto Remediation: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Auto Remediation</h1>
        <p className="text-gray-500">Automated compliance fix generation with PR-based workflows</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Wrench className="w-5 h-5 text-blue-500" />} title="Total Pipelines" value={String(stats?.total_pipelines ?? 0)} subtitle="All pipelines" />
        <StatCard icon={<GitPullRequest className="w-5 h-5 text-green-500" />} title="Fixes Generated" value={String(stats?.total_fixes_generated ?? 0)} subtitle={`${stats?.total_fixes_merged ?? 0} merged`} />
        <StatCard icon={<TrendingUp className="w-5 h-5 text-purple-500" />} title="Auto-Merge Rate" value={`${((stats?.auto_merge_rate ?? 0) * 100).toFixed(1)}%`} subtitle="Low-risk fixes" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-orange-500" />} title="Active Pipelines" value={String(stats?.by_status?.['pending'] ?? 0)} subtitle="Pending approval" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Remediation Pipelines</h2>
        {!pipelines || pipelines.length === 0 ? (
          <p className="text-gray-500">No remediation pipelines yet.</p>
        ) : (
          <div className="space-y-3">
            {pipelines.map((pipeline) => (
              <div key={pipeline.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <GitPullRequest className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{pipeline.repo}</p>
                    <p className="text-sm text-gray-500">{pipeline.violations_detected} violations · {pipeline.fixes_generated} fixes · risk: {pipeline.risk_level}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  pipeline.status === 'merged' ? 'bg-green-100 text-green-700' :
                  pipeline.status === 'pending_approval' ? 'bg-yellow-100 text-yellow-700' :
                  pipeline.status === 'rejected' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-700'
                }`}>{pipeline.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
