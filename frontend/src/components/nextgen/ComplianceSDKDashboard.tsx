'use client'

import { Code, Package, BarChart3, TrendingUp } from 'lucide-react'
import { useComplianceSdkPackages, useComplianceSdkUsage } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ComplianceSDKDashboard() {
  const { data: packages, loading: pkgLoading, error: pkgError, refetch } = useComplianceSdkPackages()
  const { data: usage, loading: usageLoading, error: usageError } = useComplianceSdkUsage()

  const loading = pkgLoading || usageLoading
  const error = pkgError || usageError

  const totalDownloads = usage?.sdk_downloads
    ? Object.values(usage.sdk_downloads).reduce((s: number, v) => s + Number(v), 0)
    : 0

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance SDK</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance SDK</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Compliance SDK: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance SDK</h1>
        <p className="text-gray-500">Compliance SDK packages for multiple programming languages</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Package className="w-5 h-5 text-blue-500" />} title="SDK Packages" value={String(packages?.length ?? 0)} subtitle="Available SDKs" />
        <StatCard icon={<TrendingUp className="w-5 h-5 text-green-500" />} title="Total Downloads" value={String(totalDownloads)} subtitle="All-time" />
        <StatCard icon={<Code className="w-5 h-5 text-purple-500" />} title="Languages" value={String(packages ? new Set(packages.map(p => p.language)).size : 0)} subtitle="Supported" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-orange-500" />} title="API Keys" value={String(usage?.total_keys ?? 0)} subtitle="Registered keys" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">SDK Packages</h2>
        {!packages || packages.length === 0 ? (
          <p className="text-gray-500">No SDK packages available.</p>
        ) : (
          <div className="space-y-3">
            {packages.map((pkg, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Code className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{pkg.name}</p>
                    <p className="text-sm text-gray-500">{pkg.language} · v{pkg.version}</p>
                  </div>
                </div>
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                  {pkg.language}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
