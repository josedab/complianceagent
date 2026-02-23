'use client'

import { Brain, TrendingUp, Target, Globe } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Privacy Regulation', detail: 'New state laws predicted', value: '89%' },
  { id: 2, name: 'AI Governance', detail: 'Framework changes expected', value: '84%' },
  { id: 3, name: 'Financial Compliance', detail: 'Basel IV impact analysis', value: '91%' },
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

export default function RegPredictionDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Prediction</h1>
        <p className="text-gray-500">Predict regulatory changes and their impact</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Brain className="h-5 w-5 text-blue-600" />} title="Models" value="8" subtitle="Active" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-green-600" />} title="Predictions" value="124" subtitle="Generated" />
        <StatCard icon={<Target className="h-5 w-5 text-purple-600" />} title="Accuracy" value="87%" subtitle="Model accuracy" />
        <StatCard icon={<Globe className="h-5 w-5 text-orange-600" />} title="Alerts" value="12" subtitle="Triggered" />
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
