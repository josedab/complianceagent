'use client'

import { Database, BarChart3, HardDrive, Activity } from 'lucide-react'
import { useDataLakeStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ComplianceDataLakeDashboard() {
  const { data: stats, loading, error, refetch } = useDataLakeStats()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Data Lake</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Data Lake</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Compliance Data Lake: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Data Lake</h1>
        <p className="text-gray-500">Centralized compliance event streaming and analytics</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Database className="w-5 h-5 text-blue-500" />} title="Total Events" value={String(stats?.total_events ?? 0)} subtitle="Compliance events" />
        <StatCard icon={<Activity className="w-5 h-5 text-orange-500" />} title="Categories" value={String(stats?.by_category ? Object.keys(stats.by_category).length : 0)} subtitle="Event categories" />
        <StatCard icon={<HardDrive className="w-5 h-5 text-green-500" />} title="Storage" value={`${(stats?.storage_size_mb ?? 0).toFixed(1)} MB`} subtitle="Data lake size" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-purple-500" />} title="Tenants" value={String(stats?.by_tenant ? Object.keys(stats.by_tenant).length : 0)} subtitle="Active tenants" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Events by Category</h2>
        {!stats || !stats.by_category || Object.keys(stats.by_category).length === 0 ? (
          <p className="text-gray-500">No data lake statistics available.</p>
        ) : (
          <div className="space-y-3">
            {Object.entries(stats.by_category).map(([category, count]) => (
              <div key={category} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <p className="font-medium text-gray-900">{category}</p>
                <span className="text-sm font-medium text-gray-700">{count.toLocaleString()} events</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
