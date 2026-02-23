'use client'

import { Award, ClipboardCheck, Shield, FileCheck } from 'lucide-react'

const MOCK_DATA = [
  { id: 1, name: 'SOC 2 Type II', detail: 'Full audit cycle — evidence collection complete', status: 'Ready (98%)' },
  { id: 2, name: 'ISO 27001', detail: 'Annex A controls mapping in progress', status: 'In Progress (72%)' },
  { id: 3, name: 'HIPAA', detail: 'Technical safeguards review pending', status: 'Pending (45%)' },
  { id: 4, name: 'PCI DSS v4.0', detail: 'SAQ-D self-assessment queued', status: 'Queued (10%)' },
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

export default function CertPipelineDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Automated Certification Pipeline</h1>
        <p className="text-gray-500">Track certification runs, readiness scores, and framework compliance</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Award className="h-5 w-5 text-blue-600" />} title="Certifications" value="4" subtitle="Active pipelines" />
        <StatCard icon={<ClipboardCheck className="h-5 w-5 text-green-600" />} title="Controls Mapped" value="187" subtitle="Across all frameworks" />
        <StatCard icon={<Shield className="h-5 w-5 text-purple-600" />} title="Avg Readiness" value="56%" subtitle="Weighted average" />
        <StatCard icon={<FileCheck className="h-5 w-5 text-orange-600" />} title="Evidence Items" value="342" subtitle="Auto-collected" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Certification Runs</h2>
        <div className="space-y-3">
          {MOCK_DATA.map((item) => (
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
