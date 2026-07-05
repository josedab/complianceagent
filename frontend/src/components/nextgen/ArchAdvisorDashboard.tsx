'use client'

import { Layout, BarChart3, Globe, Cpu } from 'lucide-react'
import { useArchAdvisorStats, useArchAdvisorFrameworks } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ArchAdvisorDashboard() {
  const { data: stats, loading: statsLoading, error: statsError, refetch } = useArchAdvisorStats()
  const { data: frameworks, loading: fwLoading, error: fwError } = useArchAdvisorFrameworks()

  const loading = statsLoading || fwLoading
  const error = statsError || fwError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Architecture Advisor</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Architecture Advisor</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Architecture Advisor: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const frameworkEntries = Object.entries(stats?.by_framework ?? {})

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Architecture Advisor</h1>
        <p className="text-gray-500">Generate compliance-ready architecture diagrams from regulations</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Layout className="w-5 h-5 text-blue-500" />} title="Total Diagrams" value={String(stats?.total_diagrams ?? 0)} subtitle="Generated diagrams" />
        <StatCard icon={<Globe className="w-5 h-5 text-green-500" />} title="Frameworks" value={String(Object.keys(stats?.by_framework ?? {}).length)} subtitle="Covered frameworks" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-purple-500" />} title="Avg Components" value={(stats?.avg_components ?? 0).toFixed(1)} subtitle="Per diagram" />
        <StatCard icon={<Cpu className="w-5 h-5 text-orange-500" />} title="Formats" value={String(Object.keys(stats?.by_format ?? {}).length)} subtitle="Output formats" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Diagrams by Framework</h2>
          {frameworkEntries.length === 0 ? (
            <p className="text-gray-500">No diagrams generated yet.</p>
          ) : (
            <div className="space-y-2">
              {frameworkEntries.map(([fw, count]) => (
                <div key={fw} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="font-medium text-gray-700">{fw}</span>
                  <span className="text-sm text-gray-500">{String(count)} diagrams</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Available Frameworks</h2>
          {!frameworks || frameworks.length === 0 ? (
            <p className="text-gray-500">No frameworks available.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {frameworks.map((fw) => (
                <span key={fw} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">{fw}</span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
