'use client'

import { Users, Zap, CheckCircle, Clock } from 'lucide-react'
import { useSwarmSessions, useSwarmStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function AgentSwarmDashboard() {
  const { data: sessions, loading: sessionsLoading, error: sessionsError, refetch } = useSwarmSessions()
  const { data: stats, loading: statsLoading, error: statsError } = useSwarmStats()

  const loading = sessionsLoading || statsLoading
  const error = sessionsError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Agentic Compliance Swarm</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Agentic Compliance Swarm</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Swarm: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Agentic Compliance Swarm</h1>
        <p className="text-gray-500">Orchestrate multi-agent compliance workflows with autonomous remediation</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Users className="w-5 h-5 text-blue-500" />} title="Active Sessions" value={String(stats?.active_sessions ?? 0)} subtitle={`${stats?.agents_deployed ?? 0} agents deployed`} />
        <StatCard icon={<Zap className="w-5 h-5 text-green-500" />} title="Total Findings" value={String(stats?.total_findings ?? 0)} subtitle="Across all sessions" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-purple-500" />} title="Total Sessions" value={String(stats?.total_sessions ?? 0)} subtitle="All time" />
        <StatCard icon={<Clock className="w-5 h-5 text-orange-500" />} title="Agents Deployed" value={String(stats?.agents_deployed ?? 0)} subtitle="Total agents" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Swarm Sessions</h2>
        {!sessions || sessions.length === 0 ? (
          <p className="text-gray-500">No swarm sessions yet.</p>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <div key={session.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Users className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{session.repo}</p>
                    <p className="text-sm text-gray-500">{session.agents.length} agents · {session.findings.length} findings · {session.frameworks.join(', ')}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  session.status === 'completed' ? 'bg-green-100 text-green-700' :
                  session.status === 'running' ? 'bg-blue-100 text-blue-700' :
                  'bg-gray-100 text-gray-700'
                }`}>{session.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
