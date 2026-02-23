'use client'

import { Network, Shield, Users, Star } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Vendor Trust Chain', detail: 'Supply chain verification', value: '98% trust' },
  { id: 2, name: 'Partner Network', detail: 'Business partner vetting', value: '95% trust' },
  { id: 3, name: 'Customer Trust', detail: 'Data handling attestation', value: '91% trust' },
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

export default function TrustNetworkDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Trust Network</h1>
        <p className="text-gray-500">Decentralized trust and reputation network</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Network className="h-5 w-5 text-blue-600" />} title="Members" value="156" subtitle="In network" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Trust Score" value="92%" subtitle="Average" />
        <StatCard icon={<Users className="h-5 w-5 text-purple-600" />} title="Attestations" value="1.8K" subtitle="Total" />
        <StatCard icon={<Star className="h-5 w-5 text-orange-600" />} title="Verified" value="134" subtitle="Organizations" />
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
