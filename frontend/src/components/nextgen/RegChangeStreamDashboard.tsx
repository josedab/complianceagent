'use client'

import { Activity, Globe, Bell, FileText } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'EU Digital Services Act', detail: 'New platform obligations', value: 'High Impact' },
  { id: 2, name: 'California SB-1047', detail: 'AI safety requirements', value: 'Medium Impact' },
  { id: 3, name: 'UK Data Reform Bill', detail: 'Privacy framework changes', value: 'High Impact' },
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

export default function RegChangeStreamDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Change Stream</h1>
        <p className="text-gray-500">Stream and track regulatory changes in real-time</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Activity className="h-5 w-5 text-blue-600" />} title="Changes" value="156" subtitle="This month" />
        <StatCard icon={<Globe className="h-5 w-5 text-green-600" />} title="Regions" value="28" subtitle="Monitored" />
        <StatCard icon={<Bell className="h-5 w-5 text-purple-600" />} title="Subscriptions" value="86" subtitle="Active" />
        <StatCard icon={<FileText className="h-5 w-5 text-orange-600" />} title="Impact" value="42" subtitle="Assessed" />
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
