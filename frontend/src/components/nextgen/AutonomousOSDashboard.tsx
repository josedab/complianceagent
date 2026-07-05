'use client'

import { Cpu, Activity, Brain, BarChart3 } from 'lucide-react'
import { useAutonomousOSEvents, useAutonomousOSStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function AutonomousOSDashboard() {
  const { data: events, loading: eventsLoading, error: eventsError, refetch } = useAutonomousOSEvents()
  const { data: stats, loading: statsLoading, error: statsError } = useAutonomousOSStats()

  const loading = eventsLoading || statsLoading
  const error = eventsError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Autonomous OS</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Autonomous OS</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Autonomous OS: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Autonomous OS</h1>
        <p className="text-gray-500">Self-managing compliance operating system with autonomous decision-making</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Activity className="w-5 h-5 text-blue-500" />} title="Total Events" value={String(stats?.total_events ?? 0)} subtitle="Events processed" />
        <StatCard icon={<Brain className="w-5 h-5 text-green-500" />} title="Decisions" value={String(stats?.total_decisions ?? 0)} subtitle={`${stats?.autonomous_decisions ?? 0} autonomous`} />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-purple-500" />} title="Avg Confidence" value={`${((stats?.avg_confidence ?? 0) * 100).toFixed(1)}%`} subtitle="Decision confidence" />
        <StatCard icon={<Cpu className="w-5 h-5 text-orange-500" />} title="Autonomy Level" value={stats?.autonomy_level ?? '-'} subtitle="Current mode" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Events</h2>
        {!events || events.length === 0 ? (
          <p className="text-gray-500">No events recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {events.slice(0, 10).map((event) => (
              <div key={event.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Activity className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{event.event_type}</p>
                    <p className="text-sm text-gray-500">Source: {event.source_service}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${event.processed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                  {event.processed ? 'Processed' : 'Pending'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
