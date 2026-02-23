'use client'

import { FlaskConical, Shield, Code, Play } from 'lucide-react'

const SANDBOXES = [
  { id: 1, name: 'Policy Sandbox', detail: 'Testing regulatory policies', status: 'Active' },
  { id: 2, name: 'Rule Engine Sandbox', detail: 'Validating compliance rules', status: 'Active' },
  { id: 3, name: 'Audit Sandbox', detail: 'Simulating audit scenarios', status: 'Idle' },
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

export default function ComplianceSandboxDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Sandbox</h1>
        <p className="text-gray-500">Isolated environments for compliance testing</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FlaskConical className="h-5 w-5 text-blue-600" />} title="Sandboxes" value="3" subtitle="Total environments" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Policies" value="12" subtitle="Under test" />
        <StatCard icon={<Code className="h-5 w-5 text-purple-600" />} title="Rules" value="48" subtitle="Configured" />
        <StatCard icon={<Play className="h-5 w-5 text-orange-600" />} title="Executions" value="156" subtitle="This week" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Sandboxes</h2>
        <div className="space-y-3">
          {SANDBOXES.map((item) => (
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
