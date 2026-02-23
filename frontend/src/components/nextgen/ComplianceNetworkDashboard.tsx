'use client'

import { Globe, Network, Users, Database } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Financial Services Hub', detail: '24 orgs sharing data', value: 'Active' },
  { id: 2, name: 'Healthcare Network', detail: '12 orgs connected', value: 'Active' },
  { id: 3, name: 'Tech Alliance', detail: '8 orgs collaborating', value: 'Growing' },
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

export default function ComplianceNetworkDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Open Compliance Data Network</h1>
        <p className="text-gray-500">Shared compliance intelligence across organizations</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Globe className="h-5 w-5 text-blue-600" />} title="Orgs" value="48" subtitle="Connected" />
        <StatCard icon={<Network className="h-5 w-5 text-green-600" />} title="Shared Rules" value="1.2K" subtitle="In network" />
        <StatCard icon={<Users className="h-5 w-5 text-purple-600" />} title="Data Points" value="15K" subtitle="Exchanged" />
        <StatCard icon={<Database className="h-5 w-5 text-orange-600" />} title="Uptime" value="99.9%" subtitle="Network health" />
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
