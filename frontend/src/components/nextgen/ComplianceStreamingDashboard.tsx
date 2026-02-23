'use client'

import { Radio, Wifi, Activity, Zap } from 'lucide-react'

const CHANNELS = [
  { id: 1, name: 'Regulatory Feed', detail: 'SEC and FINRA updates', status: 'Live' },
  { id: 2, name: 'Policy Stream', detail: 'Internal policy changes', status: 'Live' },
  { id: 3, name: 'Audit Events', detail: 'Real-time audit trail', status: 'Live' },
  { id: 4, name: 'Alert Stream', detail: 'Compliance violations', status: 'Paused' },
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

export default function ComplianceStreamingDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Real-Time Compliance Streaming</h1>
        <p className="text-gray-500">Live compliance data channels and event streams</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Radio className="h-5 w-5 text-blue-600" />} title="Channels" value="4" subtitle="Active streams" />
        <StatCard icon={<Wifi className="h-5 w-5 text-green-600" />} title="Throughput" value="1.2K" subtitle="Events/sec" />
        <StatCard icon={<Activity className="h-5 w-5 text-purple-600" />} title="Latency" value="45ms" subtitle="Avg response" />
        <StatCard icon={<Zap className="h-5 w-5 text-orange-600" />} title="Alerts" value="7" subtitle="Pending review" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Channels</h2>
        <div className="space-y-3">
          {CHANNELS.map((item) => (
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
