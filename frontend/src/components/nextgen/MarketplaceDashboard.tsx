'use client'

import { Store, Download, Star, Users, CreditCard } from 'lucide-react'
import { useMarketplaceListing, useMarketplaceInstallations } from '@/hooks/useNextgenApi'
import type { MarketplaceListing, AppInstallation, MarketplacePlan } from '@/types/nextgen'

const MOCK_LISTING: MarketplaceListing = {
  app_name: 'ComplianceAgent',
  description: 'Autonomous regulatory monitoring and compliance automation for your codebase',
  platforms: ['github', 'gitlab'],
  plans: [
    { name: 'free', display_name: 'Free', price_monthly: 0, features: ['3 frameworks', '25 PR analyses/month', '1 repository'] },
    { name: 'team', display_name: 'Team', price_monthly: 49, features: ['10 frameworks', 'Unlimited PR analyses', '10 repositories', 'Drift detection'] },
    { name: 'business', display_name: 'Business', price_monthly: 199, features: ['All frameworks', 'Unlimited repos', 'Cost calculator', 'Evidence vault', 'Priority support'] },
    { name: 'enterprise', display_name: 'Enterprise', price_monthly: 799, features: ['Everything in Business', 'SSO/SAML', 'Custom regulations', 'Dedicated support', 'SLA guarantee'] },
  ],
  total_installations: 1247,
}

const MOCK_INSTALLATIONS: AppInstallation[] = [
  { id: 'i1', platform: 'github', account_login: 'acme-corp', plan: 'business', status: 'active', repositories: ['acme/api', 'acme/web', 'acme/mobile'], installed_at: '2026-01-15T10:00:00Z' },
  { id: 'i2', platform: 'github', account_login: 'fintech-startup', plan: 'team', status: 'active', repositories: ['fintech/payments'], installed_at: '2026-02-01T14:30:00Z' },
  { id: 'i3', platform: 'gitlab', account_login: 'health-systems', plan: 'enterprise', status: 'active', repositories: ['health/ehr', 'health/portal', 'health/api', 'health/analytics'], installed_at: '2026-01-20T09:00:00Z' },
]

const planColors: Record<MarketplacePlan, string> = {
  free: 'bg-gray-100 text-gray-700', team: 'bg-blue-100 text-blue-700',
  business: 'bg-purple-100 text-purple-700', enterprise: 'bg-orange-100 text-orange-700',
}

export default function MarketplaceDashboard() {
  const { data: liveListing } = useMarketplaceListing()
  const { data: liveInstalls } = useMarketplaceInstallations()

  const listing = liveListing || MOCK_LISTING
  const installations = liveInstalls || MOCK_INSTALLATIONS

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Marketplace App</h1>
        <p className="text-gray-500">GitHub & GitLab marketplace integration management</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Download className="h-5 w-5 text-blue-600" />} title="Total Installs" value={listing.total_installations.toLocaleString()} subtitle="Across all platforms" />
        <StatCard icon={<Users className="h-5 w-5 text-green-600" />} title="Active Orgs" value={installations.filter(i => i.status === 'active').length.toString()} subtitle="Currently active" />
        <StatCard icon={<Star className="h-5 w-5 text-yellow-600" />} title="Platforms" value={listing.platforms.length.toString()} subtitle={listing.platforms.join(', ')} />
        <StatCard icon={<CreditCard className="h-5 w-5 text-purple-600" />} title="Plans" value={listing.plans.length.toString()} subtitle="Free to Enterprise" />
      </div>

      {/* Pricing Plans */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Marketplace Plans</h2>
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
      </div>

      {/* Installations */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Store className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Active Installations</h2>
        </div>
        <div className="space-y-3">
          {installations.map(inst => (
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
