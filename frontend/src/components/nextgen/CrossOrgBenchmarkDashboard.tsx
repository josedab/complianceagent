'use client'

import { BarChart3, Globe, Building, TrendingUp } from 'lucide-react'
import { useCrossOrgBenchmarkStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function CrossOrgBenchmarkDashboard() {
  const { data: stats, loading, error, refetch } = useCrossOrgBenchmarkStats()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Cross-Org Benchmark</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Cross-Org Benchmark</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Cross-Org Benchmark: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cross-Org Compliance Benchmark</h1>
        <p className="text-gray-500">Compare your compliance posture against industry peers</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Building className="w-5 h-5 text-blue-500" />} title="Participants" value={String(stats?.total_participants ?? 0)} subtitle="Benchmarked orgs" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-green-500" />} title="Global Avg" value={`${(stats?.global_avg_score ?? 0).toFixed(1)}%`} subtitle="Industry average" />
        <StatCard icon={<Globe className="w-5 h-5 text-purple-500" />} title="Industries" value={String(stats?.by_industry ? Object.keys(stats.by_industry).length : 0)} subtitle="Sectors tracked" />
        <StatCard icon={<TrendingUp className="w-5 h-5 text-orange-500" />} title="Data Age" value={`${(stats?.data_freshness_hours ?? 0).toFixed(0)}h`} subtitle="Data freshness" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Industry Breakdown</h2>
        {!stats || !stats.by_industry || Object.keys(stats.by_industry).length === 0 ? (
          <p className="text-gray-500">No benchmark data available.</p>
        ) : (
          <div className="space-y-3">
            {Object.entries(stats.by_industry).map(([industry, count]) => (
              <div key={industry} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <p className="font-medium text-gray-900">{industry}</p>
                <span className="text-sm text-gray-700">{count} organizations</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
