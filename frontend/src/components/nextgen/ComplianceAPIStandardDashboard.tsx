'use client'

import { Book, CheckCircle, BarChart3, Globe } from 'lucide-react'
import { useApiSpecVersions, useComplianceApiStandardStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ComplianceAPIStandardDashboard() {
  const { data: versions, loading: versionsLoading, error: versionsError, refetch } = useApiSpecVersions()
  const { data: stats, loading: statsLoading, error: statsError } = useComplianceApiStandardStats()

  const loading = versionsLoading || statsLoading
  const error = versionsError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance API Standard</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance API Standard</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Compliance API Standard: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance API Standard</h1>
        <p className="text-gray-500">Manage and enforce compliance API specification standards</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Book className="w-5 h-5 text-blue-500" />} title="Spec Versions" value={String(stats?.total_specs ?? 0)} subtitle="Published specs" />
        <StatCard icon={<Globe className="w-5 h-5 text-green-500" />} title="Conformance Checks" value={String(stats?.total_conformance_checks ?? 0)} subtitle="APIs checked" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-purple-500" />} title="Compliant APIs" value={String(stats?.compliant_apis ?? 0)} subtitle="Passing conformance" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-orange-500" />} title="Avg Score" value={`${(stats?.avg_compliance_score ?? 0).toFixed(1)}%`} subtitle="Conformance score" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Spec Versions</h2>
        {!versions || versions.length === 0 ? (
          <p className="text-gray-500">No spec versions published yet.</p>
        ) : (
          <div className="space-y-3">
            {versions.map((v) => (
              <div key={v.version} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Book className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">v{v.version}</p>
                    <p className="text-sm text-gray-500">Published: {v.published_at ?? 'N/A'}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${v.status === 'active' ? 'bg-green-100 text-green-700' : v.status === 'draft' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-700'}`}>
                  {v.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
