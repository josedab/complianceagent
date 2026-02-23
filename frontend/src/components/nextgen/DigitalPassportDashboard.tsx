'use client'

import { Fingerprint, Shield, CheckCircle, Link } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'EU GDPR Passport', detail: 'Data protection certification', status: 'Verified' },
  { id: 2, name: 'SOC 2 Type II', detail: 'Security compliance', status: 'Verified' },
  { id: 3, name: 'ISO 27001', detail: 'Information security', status: 'In Review' },
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

export default function DigitalPassportDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Digital Passport</h1>
        <p className="text-gray-500">Manage and verify regulatory compliance credentials</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Fingerprint className="h-5 w-5 text-blue-600" />} title="Digital IDs" value="47" subtitle="Unique identifiers issued" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Verified Passports" value="38" subtitle="Fully authenticated" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-purple-600" />} title="Checks Passed" value="156" subtitle="This quarter" />
        <StatCard icon={<Link className="h-5 w-5 text-orange-600" />} title="Linked Entities" value="23" subtitle="Cross-referenced orgs" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Passports</h2>
        <div className="space-y-3">
          {ITEMS.map((item) => (
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
