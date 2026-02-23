'use client'

import { Package, Download, Star, Users } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Compliance Scanner', detail: 'Auto-scan on PR', value: 'v2.4.1' },
  { id: 2, name: 'Policy Enforcer', detail: 'Branch protection rules', value: 'v1.8.0' },
  { id: 3, name: 'Audit Reporter', detail: 'Generate compliance reports', value: 'v3.1.2' },
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

export default function GHMarketplaceAppDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">GitHub Marketplace App</h1>
        <p className="text-gray-500">Compliance app for GitHub Marketplace distribution</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Package className="h-5 w-5 text-blue-600" />} title="Installs" value="1.2K" subtitle="Active" />
        <StatCard icon={<Download className="h-5 w-5 text-green-600" />} title="Downloads" value="8.5K" subtitle="Total" />
        <StatCard icon={<Star className="h-5 w-5 text-purple-600" />} title="Rating" value="4.8" subtitle="Out of 5" />
        <StatCard icon={<Users className="h-5 w-5 text-orange-600" />} title="Reviews" value="234" subtitle="Total" />
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
