'use client'

import { Store, Package, DollarSign, Star } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Compliance Package Pro', detail: 'Full regulatory bundle', status: 'Active' },
  { id: 2, name: 'Risk Assessment Toolkit', detail: 'Automated risk scoring', status: 'Active' },
  { id: 3, name: 'Audit Trail Manager', detail: 'Complete audit logging', status: 'Pending' },
]

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm text-gray-500">{title}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function DigitalMarketplaceB2BDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Digital Marketplace</h1>
        <p className="text-gray-500">Browse and manage B2B compliance packages</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Store className="h-5 w-5 text-blue-600" />} title="Listed Packages" value="128" subtitle="Across all categories" />
        <StatCard icon={<Package className="h-5 w-5 text-green-600" />} title="Active Subscriptions" value="34" subtitle="Currently in use" />
        <StatCard icon={<DollarSign className="h-5 w-5 text-purple-600" />} title="Monthly Revenue" value="$24.5K" subtitle="Up 12% this month" />
        <StatCard icon={<Star className="h-5 w-5 text-orange-600" />} title="Avg Rating" value="4.8" subtitle="From 512 reviews" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Featured Packages</h2>
        <div className="space-y-3">
          {ITEMS.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail}</p>
              </div>
              <span className="text-sm text-gray-600">{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
