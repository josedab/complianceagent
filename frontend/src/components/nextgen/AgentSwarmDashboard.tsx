'use client'

import { Users, Zap, CheckCircle, Clock } from 'lucide-react'

const MOCK_SESSIONS = [
  { id: 1, name: 'GDPR Data Flow Audit', agents: 8, fixes: 12, reviews: 34, avgTime: '4.2min', status: 'Completed' },
  { id: 2, name: 'SOC2 Control Validation', agents: 6, fixes: 7, reviews: 22, avgTime: '3.8min', status: 'In Progress' },
  { id: 3, name: 'HIPAA Access Review', agents: 10, fixes: 19, reviews: 45, avgTime: '5.1min', status: 'Completed' },
  { id: 4, name: 'PCI-DSS Scan Remediation', agents: 5, fixes: 3, reviews: 11, avgTime: '2.9min', status: 'Queued' },
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

export default function AgentSwarmDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Agentic Compliance Swarm</h1>
        <p className="text-gray-500">Orchestrate multi-agent compliance workflows with autonomous remediation</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Users className="w-5 h-5 text-blue-500" />} title="Active Sessions" value="4" subtitle="29 total agents deployed" />
        <StatCard icon={<Zap className="w-5 h-5 text-green-500" />} title="Auto Fixes" value="41" subtitle="Across all sessions" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-purple-500" />} title="Reviews" value="112" subtitle="Policy reviews completed" />
        <StatCard icon={<Clock className="w-5 h-5 text-orange-500" />} title="Avg Time" value="4.0min" subtitle="Per review cycle" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Swarm Sessions</h2>
        <div className="space-y-3">
          {MOCK_SESSIONS.map((session) => (
            <div key={session.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Users className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="font-medium text-gray-900">{session.name}</p>
                  <p className="text-sm text-gray-500">{session.agents} agents · {session.fixes} fixes · {session.reviews} reviews · {session.avgTime} avg</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                session.status === 'Completed' ? 'bg-green-100 text-green-700' :
                session.status === 'In Progress' ? 'bg-blue-100 text-blue-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {session.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
