'use client'

import { GitBranch, CheckCircle, AlertTriangle, Clock } from 'lucide-react'
import { useCICDChecks, useCICDStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function CICDRuntimeDashboard() {
  const { data: checks, loading: checksLoading, error: checksError, refetch } = useCICDChecks()
  const { data: stats, loading: statsLoading, error: statsError } = useCICDStats()

  const loading = checksLoading || statsLoading
  const error = checksError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">CI/CD Runtime</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">CI/CD Runtime</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading CI/CD Runtime: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">CI/CD Runtime Compliance</h1>
        <p className="text-gray-500">Compliance gates and attestations in your deployment pipelines</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<GitBranch className="w-5 h-5 text-blue-500" />} title="Total Checks" value={String(stats?.total_checks ?? 0)} subtitle="Deployment checks" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-orange-500" />} title="Gated" value={String(stats?.deployments_gated ?? 0)} subtitle="Deployments blocked" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-500" />} title="Pass Rate" value={`${((stats?.pass_rate ?? 0) * 100).toFixed(1)}%`} subtitle="Checks passing" />
        <StatCard icon={<Clock className="w-5 h-5 text-purple-500" />} title="Avg Check Time" value={`${(stats?.avg_check_duration_ms ?? 0).toFixed(0)}ms`} subtitle="Per check" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Checks</h2>
        {!checks || checks.length === 0 ? (
          <p className="text-gray-500">No deployment checks yet.</p>
        ) : (
          <div className="space-y-3">
            {checks.slice(0, 10).map((check) => (
              <div key={check.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <GitBranch className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{check.repo}</p>
                    <p className="text-sm text-gray-500">Phase: {check.phase} · {check.checks_passed} passed · {check.checks_failed} failed</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  check.gate_decision === 'allow' ? 'bg-green-100 text-green-700' :
                  check.gate_decision === 'block' ? 'bg-red-100 text-red-700' :
                  'bg-yellow-100 text-yellow-700'
                }`}>{check.gate_decision}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
