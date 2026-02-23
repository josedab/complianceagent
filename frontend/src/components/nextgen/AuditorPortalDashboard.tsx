'use client'

import { Eye, Users, FileText, Lock } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Jane Smith - EY', detail: 'SOC 2 review in progress', value: 'Active' },
  { id: 2, name: 'Mark Lee - Deloitte', detail: 'ISO audit scheduled', value: 'Pending' },
  { id: 3, name: 'Sarah Chen - PwC', detail: 'GDPR assessment complete', value: 'Done' },
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

export default function AuditorPortalDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Auditor Portal</h1>
        <p className="text-gray-500">Secure portal for external auditor collaboration</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Eye className="h-5 w-5 text-blue-600" />} title="Auditors" value="5" subtitle="Active" />
        <StatCard icon={<Users className="h-5 w-5 text-green-600" />} title="Reviews" value="12" subtitle="In progress" />
        <StatCard icon={<FileText className="h-5 w-5 text-purple-600" />} title="Documents" value="89" subtitle="Shared" />
        <StatCard icon={<Lock className="h-5 w-5 text-orange-600" />} title="Access Logs" value="342" subtitle="This week" />
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
