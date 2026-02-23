'use client'

import { Code, FileCode, Wrench, Eye } from 'lucide-react'

const MOCK_EDITOR_SESSIONS = [
  { id: 1, file: 'auth/access-control.ts', framework: 'SOC2', issues: 3, status: 'In Progress', user: 'alice@acme.com' },
  { id: 2, file: 'data/retention-policy.yaml', framework: 'GDPR', issues: 1, status: 'Review', user: 'bob@acme.com' },
  { id: 3, file: 'infra/encryption.tf', framework: 'PCI-DSS', issues: 5, status: 'In Progress', user: 'carol@acme.com' },
  { id: 4, file: 'api/audit-logging.ts', framework: 'HIPAA', issues: 0, status: 'Compliant', user: 'dave@acme.com' },
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

export default function ComplianceEditorDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance-Native Code Editor</h1>
        <p className="text-gray-500">Real-time compliance feedback during code authoring</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Code className="w-5 h-5 text-blue-500" />} title="Active Sessions" value="4" subtitle="Editors with live checks" />
        <StatCard icon={<FileCode className="w-5 h-5 text-green-500" />} title="Files Scanned" value="127" subtitle="Today across sessions" />
        <StatCard icon={<Wrench className="w-5 h-5 text-yellow-500" />} title="Auto-Fixes Applied" value="34" subtitle="Automated remediations" />
        <StatCard icon={<Eye className="w-5 h-5 text-purple-500" />} title="Issues Found" value="9" subtitle="Pending review" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Editor Sessions</h2>
        <div className="space-y-3">
          {MOCK_EDITOR_SESSIONS.map((session) => (
            <div key={session.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <FileCode className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="font-medium text-gray-900">{session.file}</p>
                  <p className="text-sm text-gray-500">{session.user} · {session.framework} · {session.issues} issues</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                session.status === 'Compliant' ? 'bg-green-100 text-green-700' :
                session.status === 'Review' ? 'bg-yellow-100 text-yellow-700' :
                'bg-blue-100 text-blue-700'
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
