'use client'

import { TrendingUp, DollarSign, Users, Activity } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'GDPR Fine Prediction', detail: 'Will fines exceed €1B?', value: '72% Yes' },
  { id: 2, name: 'AI Regulation Timeline', detail: 'US AI law by 2025?', value: '45% Yes' },
  { id: 3, name: 'SOC 2 Automation', detail: 'Full automation by 2026?', value: '88% Yes' },
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

export default function PredictionMarketDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Prediction Market</h1>
        <p className="text-gray-500">Prediction markets for compliance outcomes</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<TrendingUp className="h-5 w-5 text-blue-600" />} title="Markets" value="18" subtitle="Active" />
        <StatCard icon={<DollarSign className="h-5 w-5 text-green-600" />} title="Traders" value="156" subtitle="Participating" />
        <StatCard icon={<Users className="h-5 w-5 text-purple-600" />} title="Volume" value="$42K" subtitle="Total traded" />
        <StatCard icon={<Activity className="h-5 w-5 text-orange-600" />} title="Accuracy" value="82%" subtitle="Historical" />
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
