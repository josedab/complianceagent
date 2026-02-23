'use client'

import { Calculator, DollarSign, TrendingUp, Target } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'SOC 2 Implementation', detail: 'Full program cost estimate', value: '$340K' },
  { id: 2, name: 'GDPR Compliance', detail: 'Data protection budget', value: '$280K' },
  { id: 3, name: 'ISO 27001', detail: 'Certification costs', value: '$195K' },
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

export default function CostCalculatorDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Cost Calculator</h1>
        <p className="text-gray-500">Estimate and forecast compliance program costs</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Calculator className="h-5 w-5 text-blue-600" />} title="Estimates" value="24" subtitle="Generated" />
        <StatCard icon={<DollarSign className="h-5 w-5 text-green-600" />} title="Savings" value="$1.8M" subtitle="Identified" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-purple-600" />} title="Accuracy" value="92%" subtitle="Estimate accuracy" />
        <StatCard icon={<Target className="h-5 w-5 text-orange-600" />} title="Forecasts" value="12" subtitle="Active" />
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
