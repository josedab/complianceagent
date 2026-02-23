'use client'

import { FileText, Send, Clock, CheckCircle } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Annual SOC Report', detail: 'Due March 31', value: 'In Review' },
  { id: 2, name: 'GDPR DPA Filing', detail: 'Quarterly submission', value: 'Submitted' },
  { id: 3, name: 'PCI DSS SAQ', detail: 'Annual questionnaire', value: 'Pending' },
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

export default function RegulatoryFilingDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Filing</h1>
        <p className="text-gray-500">Automated regulatory filing and submission management</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FileText className="h-5 w-5 text-blue-600" />} title="Filings" value="86" subtitle="This year" />
        <StatCard icon={<Send className="h-5 w-5 text-green-600" />} title="Submitted" value="72" subtitle="Successfully" />
        <StatCard icon={<Clock className="h-5 w-5 text-purple-600" />} title="On Time" value="98%" subtitle="Filing rate" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-orange-600" />} title="Pending" value="14" subtitle="Due soon" />
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
