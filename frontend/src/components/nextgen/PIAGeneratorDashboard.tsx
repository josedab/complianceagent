'use client'

import { FileText, Shield, Eye, CheckCircle } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Customer Data Platform', detail: 'High-risk PII processing', value: 'Complete' },
  { id: 2, name: 'Marketing Analytics', detail: 'Cookie tracking assessment', value: 'In Review' },
  { id: 3, name: 'Employee Portal', detail: 'HR data privacy impact', value: 'Draft' },
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

export default function PIAGeneratorDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">PIA Generator</h1>
        <p className="text-gray-500">Privacy Impact Assessment generator and manager</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FileText className="h-5 w-5 text-blue-600" />} title="PIAs" value="18" subtitle="Generated" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Risk Items" value="234" subtitle="Identified" />
        <StatCard icon={<Eye className="h-5 w-5 text-purple-600" />} title="Completion" value="87%" subtitle="Average" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-orange-600" />} title="Reviewed" value="14" subtitle="Approved" />
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
