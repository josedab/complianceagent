'use client'

import { FolderOpen, CheckCircle, Clock, BarChart3 } from 'lucide-react'
import { useAuditWorkspaces } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function AuditWorkspaceDashboard() {
  const { data: workspaces, loading, error, refetch } = useAuditWorkspaces()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Audit Workspace</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Audit Workspace</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Audit Workspace: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const avgReadiness = workspaces && workspaces.length > 0
    ? workspaces.reduce((sum, w) => sum + w.readiness_pct, 0) / workspaces.length
    : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Workspace</h1>
        <p className="text-gray-500">Self-service audit preparation and evidence management</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FolderOpen className="w-5 h-5 text-blue-500" />} title="Workspaces" value={String(workspaces?.length ?? 0)} subtitle="Total workspaces" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-green-500" />} title="Avg Readiness" value={`${avgReadiness.toFixed(1)}%`} subtitle="Across all workspaces" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-purple-500" />} title="Frameworks" value={String(new Set(workspaces?.map(w => w.framework) ?? []).size)} subtitle="Unique frameworks" />
        <StatCard icon={<Clock className="w-5 h-5 text-orange-500" />} title="Phases" value={String(new Set(workspaces?.map(w => w.phase) ?? []).size)} subtitle="Active phases" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Audit Workspaces</h2>
        {!workspaces || workspaces.length === 0 ? (
          <p className="text-gray-500">No audit workspaces yet.</p>
        ) : (
          <div className="space-y-3">
            {workspaces.map((ws) => (
              <div key={ws.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <FolderOpen className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{ws.framework.toUpperCase()}</p>
                    <p className="text-sm text-gray-500">Phase: {ws.phase} · Readiness: {ws.readiness_pct.toFixed(1)}%</p>
                  </div>
                </div>
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${ws.readiness_pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
