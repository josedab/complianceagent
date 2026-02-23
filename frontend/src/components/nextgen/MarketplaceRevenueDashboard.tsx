'use client'

import { DollarSign, TrendingUp, Users, BarChart3 } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Enterprise Tier', detail: 'Full platform access', value: '$180K MRR' },
  { id: 2, name: 'Professional Tier', detail: 'Core features', value: '$78K MRR' },
  { id: 3, name: 'Starter Tier', detail: 'Basic compliance tools', value: '$27K MRR' },
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

export default function MarketplaceRevenueDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Marketplace Revenue</h1>
        <p className="text-gray-500">Revenue analytics for compliance marketplace</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<DollarSign className="h-5 w-5 text-blue-600" />} title="MRR" value="$285K" subtitle="Monthly recurring" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-green-600" />} title="Growth" value="+12%" subtitle="Month over month" />
        <StatCard icon={<Users className="h-5 w-5 text-purple-600" />} title="Customers" value="342" subtitle="Active paying" />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-orange-600" />} title="ARPU" value="$833" subtitle="Per customer" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Items</h2>
        <div className="space-y-3">
          {ITEMS.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail}</p>
              </div>
              <span className="text-sm text-gray-600">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
