'use client'

import { Radio, Users, Activity, Clock } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'SEV-1: Data Breach', detail: 'Customer data exposure', value: 'Active' },
  { id: 2, name: 'SEV-2: Auth Failure', detail: 'SSO provider outage', value: 'Monitoring' },
  { id: 3, name: 'SEV-3: Cert Expiry', detail: 'TLS certificate renewal', value: 'Resolved' },
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

export default function IncidentWarRoomDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Incident War Room</h1>
        <p className="text-gray-500">Real-time incident collaboration and command center</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Radio className="h-5 w-5 text-blue-600" />} title="Active" value="3" subtitle="Incidents" />
        <StatCard icon={<Users className="h-5 w-5 text-green-600" />} title="Responders" value="18" subtitle="On call" />
        <StatCard icon={<Activity className="h-5 w-5 text-purple-600" />} title="Uptime" value="99.2%" subtitle="This month" />
        <StatCard icon={<Clock className="h-5 w-5 text-orange-600" />} title="Avg Duration" value="4.5h" subtitle="Per incident" />
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
