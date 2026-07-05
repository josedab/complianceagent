'use client'

import { Activity, TrendingUp, AlertTriangle, BarChart3 } from 'lucide-react'
import { useObservabilityMetrics, useObservabilityStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ComplianceObservabilityDashboard() {
  const { data: metrics, loading: metricsLoading, error: metricsError, refetch } = useObservabilityMetrics()
  const { data: stats, loading: statsLoading, error: statsError } = useObservabilityStats()

  const loading = metricsLoading || statsLoading
  const error = metricsError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Observability</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Observability</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Compliance Observability: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Observability</h1>
        <p className="text-gray-500">Monitor compliance signal pipelines and metric streams</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<BarChart3 className="w-5 h-5 text-blue-500" />} title="Metrics Emitted" value={String(stats?.metrics_emitted ?? 0)} subtitle="Tracked metrics" />
        <StatCard icon={<Activity className="w-5 h-5 text-green-500" />} title="Exporters" value={String(stats?.exporters_configured ?? 0)} subtitle="Configured exporters" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-orange-500" />} title="Active Alerts" value={String(stats?.active_alerts ?? 0)} subtitle="Alert rules firing" />
        <StatCard icon={<TrendingUp className="w-5 h-5 text-purple-500" />} title="Metric Types" value={String(stats?.metrics_by_type ? Object.keys(stats.metrics_by_type).length : 0)} subtitle="Types tracked" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Metrics</h2>
        {!metrics || metrics.length === 0 ? (
          <p className="text-gray-500">No observability metrics yet.</p>
        ) : (
          <div className="space-y-3">
            {metrics.slice(0, 10).map((metric, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Activity className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{metric.name}</p>
                    <p className="text-sm text-gray-500">Type: {metric.metric_type} · Unit: {metric.unit}</p>
                  </div>
                </div>
                <span className="text-sm font-medium text-gray-700">{metric.value.toFixed(2)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
