'use client'

import { Layers, GitMerge, Globe, CheckCircle } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'SOC 2 ↔ ISO 27001', detail: '82% control overlap', value: 'Mapped' },
  { id: 2, name: 'GDPR ↔ CCPA', detail: 'Privacy regulation alignment', value: 'Mapped' },
  { id: 3, name: 'HIPAA ↔ SOC 2', detail: 'Healthcare compliance bridge', value: 'In Progress' },
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

export default function HarmonizationEngineDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Harmonization</h1>
        <p className="text-gray-500">Harmonize requirements across regulatory frameworks</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Layers className="h-5 w-5 text-blue-600" />} title="Frameworks" value="12" subtitle="Harmonized" />
        <StatCard icon={<GitMerge className="h-5 w-5 text-green-600" />} title="Mappings" value="456" subtitle="Created" />
        <StatCard icon={<Globe className="h-5 w-5 text-purple-600" />} title="Overlap" value="73%" subtitle="Control overlap" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-orange-600" />} title="Conflicts" value="18" subtitle="Resolved" />
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
