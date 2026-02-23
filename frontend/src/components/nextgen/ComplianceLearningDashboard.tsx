'use client'

import { GraduationCap, Award, Users, Clock } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'GDPR Fundamentals', detail: 'Privacy regulation basics', value: '92%' },
  { id: 2, name: 'SOC 2 Controls', detail: 'Security control implementation', value: '87%' },
  { id: 3, name: 'Risk Management', detail: 'Enterprise risk frameworks', value: '78%' },
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

export default function ComplianceLearningDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Training & Learning</h1>
        <p className="text-gray-500">Interactive compliance training and certification platform</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<GraduationCap className="h-5 w-5 text-blue-600" />} title="Courses" value="32" subtitle="Available" />
        <StatCard icon={<Award className="h-5 w-5 text-green-600" />} title="Certified" value="156" subtitle="This quarter" />
        <StatCard icon={<Users className="h-5 w-5 text-purple-600" />} title="Learners" value="420" subtitle="Active" />
        <StatCard icon={<Clock className="h-5 w-5 text-orange-600" />} title="Avg Time" value="4.2h" subtitle="Per course" />
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
