'use client'

import { Cloud, Network, Shield, Globe } from 'lucide-react'

const MOCK_ACCOUNTS = [
  { provider: 'AWS', account: 'prod-123', resources: 142, score: 88.5, status: 'compliant' },
  { provider: 'Azure', account: 'sub-456', resources: 89, score: 82.0, status: 'partial' },
  { provider: 'GCP', account: 'proj-789', resources: 67, score: 91.2, status: 'compliant' },
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

export default function CrossCloudMeshDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cross-Cloud Compliance Mesh</h1>
        <p className="text-gray-500">Unified compliance across AWS, Azure, and GCP</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Cloud className="h-5 w-5 text-blue-600" />} title="Cloud Accounts" value="3" subtitle="Connected providers" />
        <StatCard icon={<Network className="h-5 w-5 text-green-600" />} title="Resources" value="298" subtitle="Discovered resources" />
        <StatCard icon={<Shield className="h-5 w-5 text-purple-600" />} title="Compliance" value="87.2%" subtitle="Overall posture" />
        <StatCard icon={<Globe className="h-5 w-5 text-orange-600" />} title="Regions" value="12" subtitle="Active regions" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Cloud Accounts</h2>
        <div className="space-y-3">
          {MOCK_ACCOUNTS.map((acct) => (
            <div key={acct.account} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{acct.provider}</span>
                <p className="text-xs text-gray-500">{acct.account} · {acct.resources} resources</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-900">{acct.score}%</span>
                <span className={`px-2 py-0.5 text-xs rounded ${acct.status === 'compliant' ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700'}`}>{acct.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
