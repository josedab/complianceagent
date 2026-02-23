'use client'

import { CreditCard, TrendingDown, Target, DollarSign } from 'lucide-react'

const MOCK_DEBT_ITEMS = [
  { id: 1, name: 'Outdated Encryption Standards', category: 'Security', cost: '$45K', age: '6 months', priority: 'Critical' },
  { id: 2, name: 'Missing Data Retention Policies', category: 'Privacy', cost: '$28K', age: '4 months', priority: 'High' },
  { id: 3, name: 'Unpatched Vulnerability Backlog', category: 'Infrastructure', cost: '$62K', age: '8 months', priority: 'Critical' },
  { id: 4, name: 'Legacy Access Control System', category: 'Identity', cost: '$35K', age: '12 months', priority: 'Medium' },
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

export default function ComplianceDebtDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Debt Dashboard</h1>
        <p className="text-gray-500">Track and prioritize outstanding compliance remediation costs</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<CreditCard className="w-5 h-5 text-red-500" />} title="Total Debt" value="$170K" subtitle="Estimated remediation cost" />
        <StatCard icon={<TrendingDown className="w-5 h-5 text-green-500" />} title="Debt Reduction" value="18%" subtitle="vs. last quarter" />
        <StatCard icon={<Target className="w-5 h-5 text-blue-500" />} title="Items Tracked" value="4" subtitle="Active debt items" />
        <StatCard icon={<DollarSign className="w-5 h-5 text-yellow-500" />} title="Monthly Burn" value="$12K" subtitle="Interest on open items" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Compliance Debt Items</h2>
        <div className="space-y-3">
          {MOCK_DEBT_ITEMS.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <DollarSign className="w-5 h-5 text-red-500" />
                <div>
                  <p className="font-medium text-gray-900">{item.name}</p>
                  <p className="text-sm text-gray-500">{item.category} · Est. {item.cost} · Open {item.age}</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                item.priority === 'Critical' ? 'bg-red-100 text-red-700' :
                item.priority === 'High' ? 'bg-orange-100 text-orange-700' :
                'bg-yellow-100 text-yellow-700'
              }`}>
                {item.priority}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
