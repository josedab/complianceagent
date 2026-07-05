'use client'

import { Edit, CheckCircle, FileText, Wrench } from 'lucide-react'
import { useComplianceEditorStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ComplianceEditorDashboard() {
  const { data: stats, loading, error, refetch } = useComplianceEditorStats()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Editor</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Editor</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Compliance Editor: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Editor</h1>
        <p className="text-gray-500">Real-time compliance policy editing with inline validation</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Edit className="w-5 h-5 text-blue-500" />} title="Active Sessions" value={String(stats?.active_sessions ?? 0)} subtitle="Editors working now" />
        <StatCard icon={<FileText className="w-5 h-5 text-green-500" />} title="Total Sessions" value={String(stats?.total_sessions ?? 0)} subtitle="All-time" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-purple-500" />} title="Fixes Applied" value={String(stats?.total_fixes_applied ?? 0)} subtitle="Auto-applied" />
        <StatCard icon={<Wrench className="w-5 h-5 text-orange-500" />} title="Issues Found" value={String(stats?.total_issues_found ?? 0)} subtitle="Detected" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Editor Activity</h2>
        {!stats ? (
          <p className="text-gray-500">No editor activity yet.</p>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-600 font-medium">Active Sessions</p>
              <p className="text-2xl font-bold text-blue-900">{stats.active_sessions}</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-green-600 font-medium">Fixes Applied</p>
              <p className="text-2xl font-bold text-green-900">{stats.total_fixes_applied}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
