'use client'

import { DollarSign, Globe, TrendingUp, BarChart3 } from 'lucide-react'
import { useMonetizationApis, useMonetizationRevenue } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function APIMonetizationDashboard() {
  const { data: apis, loading: apisLoading, error: apisError, refetch } = useMonetizationApis()
  const { data: revenue, loading: revLoading, error: revError } = useMonetizationRevenue()

  const loading = apisLoading || revLoading
  const error = apisError || revError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">API Monetization</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">API Monetization</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading API Monetization: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">API Monetization</h1>
        <p className="text-gray-500">Manage compliance API subscriptions, usage, and revenue</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Globe className="w-5 h-5 text-blue-500" />} title="Total APIs" value={String(revenue?.total_apis ?? 0)} subtitle={`${revenue?.total_developers ?? 0} developers`} />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-green-500" />} title="Requests/Month" value={String(revenue?.total_requests_month ?? 0)} subtitle="This month" />
        <StatCard icon={<DollarSign className="w-5 h-5 text-purple-500" />} title="Monthly Revenue" value={`$${(revenue?.monthly_revenue ?? 0).toFixed(2)}`} subtitle={`Avg $${(revenue?.avg_revenue_per_api ?? 0).toFixed(2)}/api`} />
        <StatCard icon={<TrendingUp className="w-5 h-5 text-orange-500" />} title="Revenue Growth" value={`${(revenue?.revenue_growth_pct ?? 0).toFixed(1)}%`} subtitle="Month over month" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Compliance APIs</h2>
        {!apis || apis.length === 0 ? (
          <p className="text-gray-500">No APIs published yet.</p>
        ) : (
          <div className="space-y-3">
            {apis.map((api) => (
              <div key={api.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Globe className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{api.name}</p>
                    <p className="text-sm text-gray-500">{api.regulation} · {api.requests_per_month.toLocaleString()} req/mo · ${api.pricing_per_request}/req</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${api.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                  {api.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
