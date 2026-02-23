'use client'

import { Target, BarChart3, TrendingUp, Award } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Data Protection', detail: 'Privacy controls score', value: '92%' },
  { id: 2, name: 'Access Management', detail: 'IAM posture assessment', value: '85%' },
  { id: 3, name: 'Incident Response', detail: 'IR readiness score', value: '84%' },
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

export default function PostureScoringDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Posture Scoring</h1>
        <p className="text-gray-500">Continuous compliance posture scoring and benchmarking</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Target className="h-5 w-5 text-blue-600" />} title="Score" value="87%" subtitle="Current posture" />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-green-600" />} title="Controls" value="234" subtitle="Evaluated" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-purple-600" />} title="Trend" value="+5%" subtitle="Month over month" />
        <StatCard icon={<Award className="h-5 w-5 text-orange-600" />} title="Percentile" value="92nd" subtitle="Industry rank" />
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
