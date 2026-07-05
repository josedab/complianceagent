'use client'

import { Code, Package, BarChart3, Globe } from 'lucide-react'
import { useClientSDKPackages, useClientSDKStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ClientSDKDashboard() {
  const { data: packages, loading: pkgLoading, error: pkgError, refetch } = useClientSDKPackages()
  const { data: stats, loading: statsLoading, error: statsError } = useClientSDKStats()

  const loading = pkgLoading || statsLoading
  const error = pkgError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Client SDK</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Client SDK</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Client SDK: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const statsData = stats as Record<string, unknown> | null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Client SDK</h1>
        <p className="text-gray-500">Generate and manage API client SDKs for multiple runtimes</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Package className="w-5 h-5 text-blue-500" />} title="SDK Packages" value={String(statsData?.total_packages ?? packages?.length ?? 0)} subtitle="Available runtimes" />
        <StatCard icon={<Globe className="w-5 h-5 text-green-500" />} title="Endpoints" value={String(statsData?.total_endpoints ?? 0)} subtitle="API endpoints" />
        <StatCard icon={<Code className="w-5 h-5 text-purple-500" />} title="API Keys" value={String(statsData?.total_api_keys ?? 0)} subtitle="Active keys" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-orange-500" />} title="Requests" value={String(statsData?.total_requests ?? 0)} subtitle="Total requests" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">SDK Packages</h2>
        {!packages || packages.length === 0 ? (
          <p className="text-gray-500">No SDK packages available.</p>
        ) : (
          <div className="space-y-3">
            {packages.map((pkg, idx) => {
              const p = pkg as Record<string, unknown>
              return (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Code className="w-5 h-5 text-blue-500" />
                    <div>
                      <p className="font-medium text-gray-900">{String(p.runtime ?? p.name ?? 'SDK')}</p>
                      <p className="text-sm text-gray-500">{String(p.version ?? '')} · {String(p.description ?? '')}</p>
                    </div>
                  </div>
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                    {String(p.runtime ?? '')}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
