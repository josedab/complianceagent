'use client'

import { useTelemetrySnapshot, useTelemetryEvents, useHeatmapData } from '@/hooks/useTelemetry'
import { TelemetryOverview, EventFeed } from '@/components/telemetry/TelemetryWidgets'
import { Activity } from 'lucide-react'
import type { TelemetrySnapshot } from '@/types/telemetry'

const fallbackSnapshot: TelemetrySnapshot = {
  overall_score: 85.0,
  violation_count: 3,
  requirement_coverage: 78.5,
  drift_score: 3.2,
  risk_score: 22.0,
  audit_readiness: 72.0,
  frameworks: { gdpr: 88.0, hipaa: 76.0, pci_dss: 92.0, soc2: 81.0 },
  repositories: {},
  timestamp: null,
}

export default function TelemetryPage() {
  const { data: snapshot, isLoading: snapshotLoading, error: snapshotError } = useTelemetrySnapshot()
  const { data: events } = useTelemetryEvents(20)
  const { data: heatmap } = useHeatmapData('7d')

  const displaySnapshot = snapshot || fallbackSnapshot

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Compliance Telemetry</h1>
          <p className="text-gray-500">Real-time monitoring of your compliance posture</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-sm">
          <Activity className="h-4 w-4 animate-pulse" />
          <span>Live</span>
        </div>
      </div>

      {snapshotError && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <p className="text-sm text-yellow-800">Using demo data — connect backend for live telemetry</p>
        </div>
      )}

      {/* Main Telemetry Overview */}
      <TelemetryOverview snapshot={displaySnapshot} />

      {/* Heatmap & Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Heatmap */}
        <div className="card p-4">
          <h3 className="text-lg font-semibold mb-4">7-Day Compliance Heatmap</h3>
          {heatmap ? (
            <div className="space-y-2">
              {Object.entries(heatmap.frameworks).map(([fw, days]) => (
                <div key={fw} className="flex items-center gap-2">
                  <span className="w-16 text-xs font-medium text-gray-500 uppercase">{fw}</span>
                  <div className="flex gap-0.5">
                    {days.map((day, i) => {
                      const bg = day.score >= 90 ? 'bg-green-500' : day.score >= 75 ? 'bg-green-300' : day.score >= 60 ? 'bg-yellow-400' : 'bg-red-400'
                      return (
                        <div key={i} className={`w-6 h-6 rounded-sm ${bg}`} title={`${day.date}: ${day.score}%`} />
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">Loading heatmap data...</p>
          )}
        </div>

        {/* Event Feed */}
        <EventFeed events={events || []} />
      </div>
    </div>
  )
}
