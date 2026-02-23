'use client'

import { Users, CheckCircle, Clock, Star } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Enterprise Acme Corp', detail: 'Full platform setup', value: 'Day 2 of 5' },
  { id: 2, name: 'Mid-Market TechFlow', detail: 'Core module activation', value: 'Complete' },
  { id: 3, name: 'Startup DataGuard', detail: 'Basic compliance setup', value: 'Complete' },
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

export default function SaaSOnboardingDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">SaaS Onboarding</h1>
        <p className="text-gray-500">Streamlined SaaS customer onboarding for compliance</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Users className="h-5 w-5 text-blue-600" />} title="Customers" value="86" subtitle="Total" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-green-600" />} title="Onboarded" value="72" subtitle="This month" />
        <StatCard icon={<Clock className="h-5 w-5 text-purple-600" />} title="Avg Time" value="3.2d" subtitle="Time to value" />
        <StatCard icon={<Star className="h-5 w-5 text-orange-600" />} title="Satisfaction" value="4.7" subtitle="Out of 5" />
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
