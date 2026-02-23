'use client'

import { CreditCard, TrendingUp, AlertTriangle, Target } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Legacy Auth System', detail: 'Non-compliant encryption', value: '$420K' },
  { id: 2, name: 'Audit Log Gaps', detail: 'Missing 30-day retention', value: '$280K' },
  { id: 3, name: 'Access Control Debt', detail: 'RBAC not fully implemented', value: '$195K' },
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

export default function DebtSecuritizationDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Debt Securitization</h1>
        <p className="text-gray-500">Quantify and manage compliance technical debt</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<CreditCard className="h-5 w-5 text-blue-600" />} title="Debt Items" value="156" subtitle="Identified" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-green-600" />} title="Total Value" value="$3.2M" subtitle="Estimated impact" />
        <StatCard icon={<AlertTriangle className="h-5 w-5 text-purple-600" />} title="Critical" value="12" subtitle="Need attention" />
        <StatCard icon={<Target className="h-5 w-5 text-orange-600" />} title="Resolved" value="89" subtitle="This quarter" />
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
