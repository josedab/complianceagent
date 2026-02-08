'use client'

import { Activity, AlertTriangle, BarChart3, Gauge, Shield, TrendingDown, TrendingUp } from 'lucide-react'
import type { TelemetrySnapshot } from '@/types/telemetry'

export function PostureGauge({ score, label }: { score: number; label: string }) {
  const color = score >= 80 ? 'text-green-600' : score >= 60 ? 'text-yellow-600' : 'text-red-600'
  const bgColor = score >= 80 ? 'stroke-green-500' : score >= 60 ? 'stroke-yellow-500' : 'stroke-red-500'
  const circumference = 2 * Math.PI * 45
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-28 h-28">
        <svg className="w-28 h-28 transform -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="8"
            className="text-gray-200 dark:text-gray-700" />
          <circle cx="50" cy="50" r="45" fill="none" strokeWidth="8" strokeLinecap="round"
            className={bgColor} strokeDasharray={circumference} strokeDashoffset={offset} />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`text-2xl font-bold ${color}`}>{Math.round(score)}%</span>
        </div>
      </div>
      <span className="mt-2 text-sm font-medium text-gray-600 dark:text-gray-400">{label}</span>
    </div>
  )
}

export function MetricCard({
  title,
  value,
  unit,
  trend,
  icon,
}: {
  title: string
  value: number
  unit?: string
  trend?: number | null
  icon: React.ReactNode
}) {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-500">{title}</span>
        {icon}
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-gray-900 dark:text-white">
          {typeof value === 'number' ? value.toFixed(1) : value}
        </span>
        {unit && <span className="text-sm text-gray-500">{unit}</span>}
      </div>
      {trend !== undefined && trend !== null && (
        <div className={`flex items-center gap-1 mt-1 text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {trend >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
          <span>{trend >= 0 ? '+' : ''}{trend.toFixed(1)}</span>
        </div>
      )}
    </div>
  )
}

export function TelemetryOverview({ snapshot }: { snapshot: TelemetrySnapshot }) {
  return (
    <div className="space-y-6">
      {/* Gauges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <PostureGauge score={snapshot.overall_score} label="Overall Score" />
        <PostureGauge score={snapshot.requirement_coverage} label="Coverage" />
        <PostureGauge score={snapshot.audit_readiness} label="Audit Ready" />
        <PostureGauge score={100 - snapshot.risk_score} label="Risk Posture" />
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Violations (24h)"
          value={snapshot.violation_count}
          icon={<AlertTriangle className="h-5 w-5 text-red-500" />}
        />
        <MetricCard
          title="Drift Score"
          value={snapshot.drift_score}
          unit="%"
          icon={<Activity className="h-5 w-5 text-yellow-500" />}
        />
        <MetricCard
          title="Risk Score"
          value={snapshot.risk_score}
          unit="/100"
          icon={<Shield className="h-5 w-5 text-blue-500" />}
        />
        <MetricCard
          title="Audit Readiness"
          value={snapshot.audit_readiness}
          unit="%"
          icon={<Gauge className="h-5 w-5 text-green-500" />}
        />
      </div>

      {/* Framework Scores */}
      {Object.keys(snapshot.frameworks).length > 0 && (
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="h-5 w-5 text-primary-600" />
            <h3 className="text-lg font-semibold">Framework Scores</h3>
          </div>
          <div className="space-y-3">
            {Object.entries(snapshot.frameworks).map(([fw, score]) => (
              <div key={fw} className="flex items-center gap-3">
                <span className="w-24 text-sm font-medium text-gray-600 uppercase">{fw}</span>
                <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${score}%` }}
                  />
                </div>
                <span className="w-12 text-sm font-medium text-right">{score.toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export function EventFeed({ events }: { events: Array<{ id: string; event_type: string; severity: string; title: string; description: string; timestamp: string | null }> }) {
  const severityColors: Record<string, string> = {
    info: 'bg-blue-100 text-blue-800',
    warning: 'bg-yellow-100 text-yellow-800',
    critical: 'bg-red-100 text-red-800',
  }

  return (
    <div className="card p-4">
      <h3 className="text-lg font-semibold mb-4">Live Event Feed</h3>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {events.length === 0 ? (
          <p className="text-sm text-gray-500">No events yet</p>
        ) : (
          events.map((event) => (
            <div key={event.id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityColors[event.severity] || severityColors.info}`}>
                {event.severity}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{event.title}</p>
                <p className="text-xs text-gray-500 truncate">{event.description}</p>
              </div>
              {event.timestamp && (
                <span className="text-xs text-gray-400 whitespace-nowrap">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
