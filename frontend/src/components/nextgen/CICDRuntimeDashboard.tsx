'use client'

import { Play, Shield, RotateCcw, Award } from 'lucide-react'

const MOCK_DATA = [
  { id: 1, name: 'deploy-prod-api v2.4.1', status: 'passed', attestation: true, timestamp: '3 min ago' },
  { id: 2, name: 'deploy-staging-web v1.8.0', status: 'passed', attestation: true, timestamp: '18 min ago' },
  { id: 3, name: 'deploy-prod-worker v3.1.0', status: 'rolled-back', attestation: false, timestamp: '42 min ago' },
  { id: 4, name: 'deploy-prod-api v2.4.0', status: 'passed', attestation: true, timestamp: '1 hr ago' },
  { id: 5, name: 'deploy-staging-api v2.4.1-rc1', status: 'passed', attestation: true, timestamp: '2 hr ago' },
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

export default function CICDRuntimeDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance-Aware CI/CD Runtime</h1>
        <p className="text-gray-500">Real-time compliance checks and attestations integrated into deployment pipelines</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Play className="h-5 w-5 text-blue-600" />} title="Checks Run" value="87" subtitle="Compliance checks this week" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Attestations" value="72" subtitle="Signed compliance attestations" />
        <StatCard icon={<RotateCcw className="h-5 w-5 text-purple-600" />} title="Rollbacks" value="4" subtitle="Non-compliant deploys reverted" />
        <StatCard icon={<Award className="h-5 w-5 text-orange-600" />} title="Pass Rate" value="95%" subtitle="Deployment compliance pass rate" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Deployment Checks</h2>
        <div className="space-y-3">
          {MOCK_DATA.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.attestation ? 'Attestation signed' : 'No attestation'} — {item.timestamp}</p>
              </div>
              <span className="text-sm text-gray-600">{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
