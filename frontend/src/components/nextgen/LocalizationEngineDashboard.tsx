'use client'

import { Globe, FileText, Clock, CheckCircle } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'GDPR German', detail: 'Full regulation translation', value: 'Complete' },
  { id: 2, name: 'SOC 2 Japanese', detail: 'Control descriptions', value: 'In Progress' },
  { id: 3, name: 'ISO 27001 French', detail: 'Framework localization', value: 'Pending' },
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

export default function LocalizationEngineDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Localization Engine</h1>
        <p className="text-gray-500">Multi-language compliance content localization</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Globe className="h-5 w-5 text-blue-600" />} title="Languages" value="24" subtitle="Supported" />
        <StatCard icon={<FileText className="h-5 w-5 text-green-600" />} title="Translations" value="12K" subtitle="Completed" />
        <StatCard icon={<Clock className="h-5 w-5 text-purple-600" />} title="Accuracy" value="97%" subtitle="Translation quality" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-orange-600" />} title="Pending" value="45" subtitle="In queue" />
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
