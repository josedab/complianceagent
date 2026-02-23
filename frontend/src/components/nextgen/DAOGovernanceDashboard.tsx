'use client'

import { Users, Shield, Activity, Star } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Update Privacy Policy', detail: 'Voting ends in 3 days', value: '78%' },
  { id: 2, name: 'Add SOC 2 Controls', detail: 'Community proposal', value: '92%' },
  { id: 3, name: 'Budget Allocation Q2', detail: 'Treasury management', value: '65%' },
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

export default function DAOGovernanceDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance DAO Governance</h1>
        <p className="text-gray-500">Decentralized governance for compliance decisions</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Users className="h-5 w-5 text-blue-600" />} title="Proposals" value="34" subtitle="Active" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Voters" value="128" subtitle="Registered" />
        <StatCard icon={<Activity className="h-5 w-5 text-purple-600" />} title="Approval Rate" value="87%" subtitle="Average" />
        <StatCard icon={<Star className="h-5 w-5 text-orange-600" />} title="Treasury" value="$450K" subtitle="Balance" />
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
