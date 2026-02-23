'use client'

import { DollarSign, TrendingUp, Calculator, BarChart3 } from 'lucide-react'

const INVESTMENTS = [
  { id: 1, name: 'Automated Monitoring', detail: 'Real-time compliance tracking', status: 'High ROI' },
  { id: 2, name: 'Policy Engine Upgrade', detail: 'Rule processing optimization', status: 'Medium ROI' },
  { id: 3, name: 'Training Program', detail: 'Staff compliance certification', status: 'High ROI' },
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

export default function CostBenefitAnalyzerDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Cost-Benefit Analyzer</h1>
        <p className="text-gray-500">ROI analysis for compliance investments</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<DollarSign className="h-5 w-5 text-blue-600" />} title="Total Cost" value="$240K" subtitle="Annual spend" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-green-600" />} title="ROI" value="3.2x" subtitle="Return ratio" />
        <StatCard icon={<Calculator className="h-5 w-5 text-purple-600" />} title="Savings" value="$180K" subtitle="Risk avoided" />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-orange-600" />} title="Projects" value="3" subtitle="Active investments" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Investments</h2>
        <div className="space-y-3">
          {INVESTMENTS.map((item) => (
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
