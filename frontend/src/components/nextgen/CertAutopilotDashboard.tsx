'use client'

import { Award, ClipboardCheck, Shield, FileCheck } from 'lucide-react'

const MOCK_DATA = [
  { id: 1, name: 'SOC2 Type II Certification', status: 'in-progress', controlsMet: 84, gaps: 3 },
  { id: 2, name: 'ISO 27001 Recertification', status: 'ready', controlsMet: 114, gaps: 0 },
  { id: 3, name: 'HIPAA Annual Review', status: 'in-progress', controlsMet: 42, gaps: 5 },
  { id: 4, name: 'PCI-DSS v4.0 Upgrade', status: 'planning', controlsMet: 28, gaps: 12 },
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

export default function CertAutopilotDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Certification Autopilot</h1>
        <p className="text-gray-500">Automated certification readiness tracking and gap analysis across frameworks</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Award className="h-5 w-5 text-blue-600" />} title="Cert Runs" value="4" subtitle="Active certification runs" />
        <StatCard icon={<ClipboardCheck className="h-5 w-5 text-green-600" />} title="Controls Met" value="268" subtitle="Total controls satisfied" />
        <StatCard icon={<Shield className="h-5 w-5 text-purple-600" />} title="Gaps Found" value="20" subtitle="Controls needing attention" />
        <StatCard icon={<FileCheck className="h-5 w-5 text-orange-600" />} title="Readiness" value="93%" subtitle="Overall certification readiness" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Certification Runs</h2>
        <div className="space-y-3">
          {MOCK_DATA.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.controlsMet} controls met · {item.gaps} gaps</p>
              </div>
              <span className="text-sm text-gray-600">{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
