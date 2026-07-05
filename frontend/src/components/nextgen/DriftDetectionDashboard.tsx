'use client'

import { Activity, AlertTriangle, CheckCircle, TrendingDown, Bell } from 'lucide-react'
import { useDriftEvents, useDriftAlerts } from '@/hooks/useNextgenApi'
import type { DriftSeverity } from '@/types/nextgen'

const severityColors: Record<DriftSeverity, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  low: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
}

export default function DriftDetectionDashboard() {
  const { data: events, loading: eventsLoading, error: eventsError, refetch: refetchEvents } = useDriftEvents()
  const { data: alerts, loading: alertsLoading, error: alertsError } = useDriftAlerts()

  const loading = eventsLoading || alertsLoading
  const error = eventsError || alertsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}
        </div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Compliance Drift Detection</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading drift events: {error.message}</p>
          <button onClick={refetchEvents} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const items = events || []
  const baselineScore = items.length > 0 ? Math.max(...items.map(e => e.previous_score)) : null
  const currentScore = items.length > 0 ? Math.min(...items.map(e => e.current_score)) : null
  const criticalCount = items.filter(e => e.severity === 'critical').length
  const highCount = items.filter(e => e.severity === 'high').length
  const alertsActive = (alerts || []).length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Drift Detection</h1>
        <p className="text-gray-500">Monitor and auto-remediate compliance regressions</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Baseline Score</p>
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{baselineScore !== null ? `${baselineScore}%` : 'N/A'}</p>
          <p className="mt-1 text-sm text-gray-500">Highest recorded pre-drift score</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Current Score</p>
            <TrendingDown className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{currentScore !== null ? `${currentScore}%` : 'N/A'}</p>
          <p className="mt-1 text-sm text-red-500">
            {baselineScore !== null && currentScore !== null ? `-${(baselineScore - currentScore).toFixed(1)} from baseline` : 'No drift events yet'}
          </p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Drift Events</p>
            <Activity className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{items.length}</p>
          <p className="mt-1 text-sm text-gray-500">{criticalCount} critical, {highCount} high</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Alert Channels</p>
            <Bell className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">{alertsActive}</p>
          <p className="mt-1 text-sm text-gray-500">Configured channels</p>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          <h2 className="text-lg font-semibold text-gray-900">Drift Events</h2>
        </div>
        {items.length === 0 ? (
          <p className="text-gray-500 text-sm">No drift events detected.</p>
        ) : (
          <div className="space-y-3">
            {[...items]
              .sort((a, b) => new Date(b.detected_at || 0).getTime() - new Date(a.detected_at || 0).getTime())
              .map(event => {
                const colors = severityColors[event.severity] || severityColors.medium
                const delta = event.current_score - event.previous_score
                return (
                  <div key={event.id} className={`p-4 rounded-lg border ${colors.border} ${colors.bg}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${colors.text} bg-white`}>{event.severity}</span>
                        <span className="px-2 py-0.5 bg-white text-gray-600 text-xs rounded-full">{event.drift_type.replace('_', ' ')}</span>
                        <span className="px-2 py-0.5 bg-white text-gray-600 text-xs rounded-full">{event.repo}</span>
                      </div>
                      <span className="text-sm text-gray-500">{event.detected_at ? new Date(event.detected_at).toLocaleString() : 'Unknown time'}</span>
                    </div>
                    <p className={`font-medium ${colors.text}`}>{event.description}</p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      <span>Baseline: {event.previous_score}%</span>
                      <span>→</span>
                      <span className="text-red-600 font-medium">Current: {event.current_score}%</span>
                      <span className="text-red-600">(Δ {delta.toFixed(1)})</span>
                      {event.resolved_at && <span className="text-green-600">Resolved</span>}
                    </div>
                  </div>
                )
              })}
          </div>
        )}
      </div>
    </div>
  )
}
