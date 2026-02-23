'use client'

import { Cpu, Zap, Shield, Activity } from 'lucide-react'

const MOCK_DATA = [
  { id: 1, name: 'Policy enforcement on deploy-prod', status: 'decided', timestamp: '1 min ago', detail: 'Blocked non-compliant image' },
  { id: 2, name: 'Auto-scaling compliance checks', status: 'auto-fixed', timestamp: '5 min ago', detail: 'Added missing audit log' },
  { id: 3, name: 'Runtime policy violation detected', status: 'escalated', timestamp: '12 min ago', detail: 'Privileged container flagged' },
  { id: 4, name: 'Certificate rotation orchestrated', status: 'decided', timestamp: '28 min ago', detail: 'Rotated 12 service certs' },
  { id: 5, name: 'Access review automation triggered', status: 'auto-fixed', timestamp: '45 min ago', detail: 'Revoked 3 stale permissions' },
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

export default function AutonomousOSDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Autonomous OS</h1>
        <p className="text-gray-500">Intelligent orchestration layer managing compliance decisions and automated responses</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Cpu className="h-5 w-5 text-blue-600" />} title="Events" value="148" subtitle="Orchestration events this week" />
        <StatCard icon={<Zap className="h-5 w-5 text-green-600" />} title="Decisions" value="92" subtitle="Autonomous decisions made" />
        <StatCard icon={<Shield className="h-5 w-5 text-purple-600" />} title="Auto-Fixes" value="67" subtitle="Issues resolved automatically" />
        <StatCard icon={<Activity className="h-5 w-5 text-orange-600" />} title="Escalations" value="11" subtitle="Escalated to human review" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Orchestration Events</h2>
        <div className="space-y-3">
          {MOCK_DATA.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail} — {item.timestamp}</p>
              </div>
              <span className="text-sm text-gray-600">{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
