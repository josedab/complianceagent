'use client'

import { Medal, Star, TrendingUp, Users } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Security Champion', detail: 'Complete all security training', value: 'Gold' },
  { id: 2, name: 'Audit Master', detail: 'Pass 10 audits consecutively', value: 'Silver' },
  { id: 3, name: 'Policy Expert', detail: 'Create 5 approved policies', value: 'Bronze' },
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

export default function GamificationEngineDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Gamification</h1>
        <p className="text-gray-500">Gamified compliance engagement and tracking</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Medal className="h-5 w-5 text-blue-600" />} title="Points" value="48K" subtitle="Total earned" />
        <StatCard icon={<Star className="h-5 w-5 text-green-600" />} title="Badges" value="156" subtitle="Awarded" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-purple-600" />} title="Streak" value="21d" subtitle="Best streak" />
        <StatCard icon={<Users className="h-5 w-5 text-orange-600" />} title="Players" value="320" subtitle="Active" />
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
