'use client'

import { FileCheck, Shield, Clock, CheckCircle } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'SOC 2 Type II', detail: 'Evidence collection 90% complete', value: '90%' },
  { id: 2, name: 'ISO 27001', detail: 'Controls mapping verified', value: '85%' },
  { id: 3, name: 'GDPR Assessment', detail: 'Data flow documented', value: '78%' },
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

export default function AuditAutopilotDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Preparation Autopilot</h1>
        <p className="text-gray-500">Automated audit preparation and evidence collection</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FileCheck className="h-5 w-5 text-blue-600" />} title="Audits" value="8" subtitle="In progress" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Evidence" value="234" subtitle="Items collected" />
        <StatCard icon={<Clock className="h-5 w-5 text-purple-600" />} title="Readiness" value="96%" subtitle="Overall score" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-orange-600" />} title="Avg Time" value="2.1d" subtitle="Per audit" />
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
