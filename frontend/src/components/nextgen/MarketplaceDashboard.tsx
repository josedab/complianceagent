'use client'

import { Store, Download, Star, Users, CreditCard } from 'lucide-react'
import { useMarketplaceListing, useMarketplaceInstallations } from '@/hooks/useNextgenApi'
import type { MarketplacePlan } from '@/types/nextgen'

const planColors: Record<MarketplacePlan, string> = {
  free: 'bg-gray-100 text-gray-700', team: 'bg-blue-100 text-blue-700',
  business: 'bg-purple-100 text-purple-700', enterprise: 'bg-orange-100 text-orange-700',
}

export default function MarketplaceDashboard() {
  const { data: listing, loading: listingLoading, error: listingError, refetch: refetchListing } = useMarketplaceListing()
  const { data: installations, loading: installsLoading, error: installsError, refetch: refetchInstalls } = useMarketplaceInstallations()

  const loading = listingLoading || installsLoading
  const error = listingError || installsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
        </div>
        <div className="card h-64 animate-pulse bg-gray-100" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading Marketplace: {error.message}</p>
        <button onClick={() => { refetchListing(); refetchInstalls(); }} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const installs = installations ?? []
  const activeInstalls = installs.filter(i => i.status === 'active')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Marketplace App</h1>
        <p className="text-gray-500">GitHub & GitLab marketplace integration management</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Download className="h-5 w-5 text-blue-600" />} title="Total Installs" value={(listing?.total_installations ?? 0).toLocaleString()} subtitle="Across all platforms" />
        <StatCard icon={<Users className="h-5 w-5 text-green-600" />} title="Active Orgs" value={activeInstalls.length.toString()} subtitle="Currently active" />
        <StatCard icon={<Star className="h-5 w-5 text-yellow-600" />} title="Platforms" value={(listing?.platforms.length ?? 0).toString()} subtitle={listing?.platforms.join(', ') ?? '—'} />
        <StatCard icon={<CreditCard className="h-5 w-5 text-purple-600" />} title="Plans" value={(listing?.plans.length ?? 0).toString()} subtitle="Free to Enterprise" />
      </div>

      {/* Pricing Plans */}
      {listing && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Marketplace Plans</h2>
          {listing.plans.length === 0 ? (
            <p className="text-gray-500 text-sm">No plans available.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {listing.plans.map(plan => (
                <div key={plan.name} className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 transition-colors">
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${planColors[plan.name]}`}>{plan.display_name}</span>
                  <p className="text-2xl font-bold text-gray-900 mt-3">
                    {plan.price_monthly === 0 ? 'Free' : `$${plan.price_monthly}`}
                    {plan.price_monthly > 0 && <span className="text-sm text-gray-500 font-normal">/mo</span>}
                  </p>
                  <ul className="mt-3 space-y-2">
                    {plan.features.map(f => (
                      <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                        <span className="text-green-500">✓</span> {f}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Installations */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Store className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Active Installations</h2>
        </div>
        {installs.length === 0 ? (
          <p className="text-gray-500 text-sm">No installations yet.</p>
        ) : (
          <div className="space-y-3">
            {installs.map(inst => (
              <div key={inst.id} className="p-3 rounded-lg border border-gray-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{inst.account_login}</span>
                    <span className={`px-2 py-0.5 text-xs rounded-full ${planColors[inst.plan]}`}>{inst.plan}</span>
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">{inst.platform}</span>
                  </div>
                  <span className="text-sm text-gray-500">{inst.repositories.length} repos</span>
                </div>
                <div className="flex gap-1 mt-2">
                  {inst.repositories.map(r => <span key={r} className="px-2 py-0.5 bg-gray-50 text-gray-600 text-xs rounded">{r}</span>)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between"><p className="text-sm font-medium text-gray-500">{title}</p>{icon}</div>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
    </div>
  )
}
