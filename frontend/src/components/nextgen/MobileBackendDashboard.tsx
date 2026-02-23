'use client'

import { Monitor, Server, Zap, Users } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Auth Service', detail: 'Mobile authentication API', value: '99.9% uptime' },
  { id: 2, name: 'Sync Engine', detail: 'Offline data synchronization', value: '99.7% uptime' },
  { id: 3, name: 'Push Notifications', detail: 'Compliance alert delivery', value: '99.8% uptime' },
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

export default function MobileBackendDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Mobile Backend</h1>
        <p className="text-gray-500">Backend services for mobile compliance applications</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Monitor className="h-5 w-5 text-blue-600" />} title="Endpoints" value="48" subtitle="Active" />
        <StatCard icon={<Server className="h-5 w-5 text-green-600" />} title="Requests" value="125K" subtitle="Daily" />
        <StatCard icon={<Zap className="h-5 w-5 text-purple-600" />} title="Uptime" value="99.8%" subtitle="Last 90 days" />
        <StatCard icon={<Users className="h-5 w-5 text-orange-600" />} title="Users" value="1.2K" subtitle="Mobile active" />
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
