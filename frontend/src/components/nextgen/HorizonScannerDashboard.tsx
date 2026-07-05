'use client'

import { Radar, Calendar, AlertTriangle, Globe } from 'lucide-react'
import { useHorizonTimeline } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function HorizonScannerDashboard() {
  const { data: timeline, loading, error, refetch } = useHorizonTimeline()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Horizon Scanner</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Horizon Scanner</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Horizon Scanner: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const upcoming = (timeline?.upcoming ?? []) as Record<string, unknown>[]
  const alerts = (timeline?.alerts ?? []) as Record<string, unknown>[]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Horizon Scanner</h1>
        <p className="text-gray-500">Track upcoming regulatory changes and compliance deadlines</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Radar className="w-5 h-5 text-blue-500" />} title="Total Tracked" value={String(timeline?.total_tracked ?? 0)} subtitle="Regulatory events" />
        <StatCard icon={<Calendar className="w-5 h-5 text-green-500" />} title="Upcoming" value={String(upcoming.length)} subtitle="Future events" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-orange-500" />} title="High Impact" value={String(timeline?.high_impact_count ?? 0)} subtitle="Critical changes" />
        <StatCard icon={<Globe className="w-5 h-5 text-purple-500" />} title="Alerts" value={String(alerts.length)} subtitle="Active alerts" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Regulatory Events</h2>
        {upcoming.length === 0 ? (
          <p className="text-gray-500">No upcoming regulatory events.</p>
        ) : (
          <div className="space-y-3">
            {upcoming.slice(0, 10).map((event, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{String(event.title ?? event.name ?? 'Event')}</p>
                    <p className="text-sm text-gray-500">{String(event.regulation ?? '')} · {String(event.effective_date ?? event.date ?? '')}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  String(event.impact ?? event.severity) === 'high' ? 'bg-red-100 text-red-700' :
                  String(event.impact ?? event.severity) === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-green-100 text-green-700'
                }`}>{String(event.impact ?? event.severity ?? 'low')}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
