'use client'

import { Map, Target, BarChart3, Brain } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Regulation Change', detail: 'Impact of new EU rules', value: '3 outcomes' },
  { id: 2, name: 'Budget Reduction', detail: '20% cut scenario', value: '4 outcomes' },
  { id: 3, name: 'Team Expansion', detail: 'Scaling compliance team', value: '3 outcomes' },
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

export default function ScenarioPlannerDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Scenario Planner</h1>
        <p className="text-gray-500">Plan and model compliance scenarios and outcomes</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Map className="h-5 w-5 text-blue-600" />} title="Scenarios" value="24" subtitle="Modeled" />
        <StatCard icon={<Target className="h-5 w-5 text-green-600" />} title="Outcomes" value="86" subtitle="Predicted" />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-purple-600" />} title="Best Case" value="94%" subtitle="Compliance score" />
        <StatCard icon={<Brain className="h-5 w-5 text-orange-600" />} title="Risk Level" value="Low" subtitle="Current" />
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
