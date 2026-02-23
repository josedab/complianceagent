'use client'

import { FileSearch, Scale, AlertCircle, CheckCircle } from 'lucide-react'

const CONTRACTS = [
  { id: 1, name: 'Vendor Agreement Q4', detail: 'Third-party data processing', status: 'Reviewed' },
  { id: 2, name: 'SLA Compliance', detail: 'Service level obligations', status: 'Pending' },
  { id: 3, name: 'NDA Template', detail: 'Confidentiality terms', status: 'Reviewed' },
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

export default function ContractAnalyzerDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Contract Analyzer</h1>
        <p className="text-gray-500">AI-powered contract review and compliance checks</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FileSearch className="h-5 w-5 text-blue-600" />} title="Contracts" value="3" subtitle="Under analysis" />
        <StatCard icon={<Scale className="h-5 w-5 text-green-600" />} title="Clauses" value="87" subtitle="Analyzed" />
        <StatCard icon={<AlertCircle className="h-5 w-5 text-purple-600" />} title="Risks" value="5" subtitle="Flagged items" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-orange-600" />} title="Compliant" value="92%" subtitle="Compliance rate" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Contracts</h2>
        <div className="space-y-3">
          {CONTRACTS.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail}</p>
              </div>
              <span className="text-sm text-gray-600">{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
