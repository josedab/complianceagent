'use client'

import { ShoppingBag, Package, TrendingUp, Star } from 'lucide-react'
import { usePolicyPacks, usePolicyMarketplaceStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function PolicyMarketplaceDashboard() {
  const { data: packs, loading: packsLoading, error: packsError, refetch } = usePolicyPacks()
  const { data: stats, loading: statsLoading, error: statsError } = usePolicyMarketplaceStats()

  const loading = packsLoading || statsLoading
  const error = packsError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Policy Marketplace</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Policy Marketplace</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Policy Marketplace: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Policy Marketplace</h1>
        <p className="text-gray-500">Browse and install compliance policy packs for your organization</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Package className="w-5 h-5 text-blue-500" />} title="Policy Packs" value={String(stats?.total_packs ?? 0)} subtitle="Available packs" />
        <StatCard icon={<TrendingUp className="w-5 h-5 text-green-500" />} title="Downloads" value={String(stats?.total_downloads ?? 0)} subtitle="All-time installs" />
        <StatCard icon={<ShoppingBag className="w-5 h-5 text-purple-500" />} title="Creators" value={String(stats?.total_creators ?? 0)} subtitle="Pack authors" />
        <StatCard icon={<Star className="w-5 h-5 text-yellow-500" />} title="GMV" value={`$${(stats?.total_gmv_usd ?? 0).toLocaleString(undefined, {maximumFractionDigits: 0})}`} subtitle="Total marketplace value" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Policy Packs</h2>
        {!packs || packs.length === 0 ? (
          <p className="text-gray-500">No policy packs available yet.</p>
        ) : (
          <div className="space-y-3">
            {packs.map((pack) => (
              <div key={pack.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Package className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{pack.title}</p>
                    <p className="text-sm text-gray-500">v{pack.version} · {pack.regulations.join(', ')} · {pack.downloads.toLocaleString()} downloads</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${pack.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                  {pack.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
