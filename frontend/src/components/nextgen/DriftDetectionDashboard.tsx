'use client'

import { Activity, AlertTriangle, CheckCircle, TrendingDown, Bell } from 'lucide-react'
import { useDriftReport } from '@/hooks/useNextgenApi'
import type { DriftEvent, DriftBaseline, DriftSeverity } from '@/types/nextgen'

const MOCK_BASELINE: DriftBaseline = {
  id: 'bl-001', repo: 'acme/payments-api', branch: 'main', score: 92.5, captured_at: '2026-02-10T10:00:00Z',
}

const MOCK_EVENTS: DriftEvent[] = [
  { id: 'de1', repo: 'acme/payments-api', drift_type: 'regression', severity: 'high', description: 'New API endpoint bypasses GDPR consent check', baseline_score: 92.5, current_score: 78.0, delta: -14.5, detected_at: '2026-02-12T14:30:00Z' },
  { id: 'de2', repo: 'acme/payments-api', drift_type: 'configuration_change', severity: 'medium', description: 'Encryption algorithm downgraded in config', baseline_score: 92.5, current_score: 85.0, delta: -7.5, detected_at: '2026-02-11T09:15:00Z' },
  { id: 'de3', repo: 'acme/payments-api', drift_type: 'policy_violation', severity: 'critical', description: 'PHI retention period exceeds 30-day policy', baseline_score: 92.5, current_score: 70.0, delta: -22.5, detected_at: '2026-02-13T08:00:00Z' },
]

const severityColors: Record<DriftSeverity, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  low: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
}

export default function DriftDetectionDashboard() {
  const { data: liveReport } = useDriftReport('current-repo')

  const events = liveReport?.events || MOCK_EVENTS
  const baseline = liveReport?.baseline || MOCK_BASELINE
  const currentScore = events.length > 0 ? Math.min(...events.map(e => e.current_score)) : baseline.score
  const criticalCount = events.filter(e => e.severity === 'critical').length
  const highCount = events.filter(e => e.severity === 'high').length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Drift Detection</h1>
        <p className="text-gray-500">Monitor and auto-remediate compliance regressions</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Baseline Score</p>
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{baseline.score}%</p>
          <p className="mt-1 text-sm text-gray-500">Captured {new Date(baseline.captured_at).toLocaleDateString()}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Current Score</p>
            <TrendingDown className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{currentScore}%</p>
          <p className="mt-1 text-sm text-red-500">-{(baseline.score - currentScore).toFixed(1)} from baseline</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Drift Events</p>
            <Activity className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{events.length}</p>
          <p className="mt-1 text-sm text-gray-500">{criticalCount} critical, {highCount} high</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Alerts Active</p>
            <Bell className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">{criticalCount + highCount}</p>
          <p className="mt-1 text-sm text-gray-500">Requiring attention</p>
        </div>
      </div>

      {/* Events */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          <h2 className="text-lg font-semibold text-gray-900">Drift Events</h2>
        </div>
        <div className="space-y-3">
          {events.sort((a, b) => new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime()).map(event => {
            const colors = severityColors[event.severity]
            return (
              <div key={event.id} className={`p-4 rounded-lg border ${colors.border} ${colors.bg}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${colors.text} bg-white`}>{event.severity}</span>
                    <span className="px-2 py-0.5 bg-white text-gray-600 text-xs rounded-full">{event.drift_type.replace('_', ' ')}</span>
                  </div>
                  <span className="text-sm text-gray-500">{new Date(event.detected_at).toLocaleString()}</span>
                </div>
                <p className={`font-medium ${colors.text}`}>{event.description}</p>
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                  <span>Baseline: {event.baseline_score}%</span>
                  <span>→</span>
                  <span className="text-red-600 font-medium">Current: {event.current_score}%</span>
                  <span className="text-red-600">(Δ {event.delta.toFixed(1)})</span>
                </div>
                <div className="mt-3">
                  <button className="px-3 py-1 bg-white border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50">
                    Auto-Remediate
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
