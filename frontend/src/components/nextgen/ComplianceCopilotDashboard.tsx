'use client'

import { Bot, AlertTriangle, CheckCircle, BookOpen } from 'lucide-react'

const MOCK_VIOLATIONS = [
  { id: 1, rule: 'GDPR Art. 17 – Right to Erasure', severity: 'Critical', status: 'Open', detectedAt: '2024-03-15' },
  { id: 2, rule: 'SOC2 CC6.1 – Logical Access', severity: 'High', status: 'In Review', detectedAt: '2024-03-14' },
  { id: 3, rule: 'HIPAA §164.312 – Access Control', severity: 'Medium', status: 'Remediated', detectedAt: '2024-03-12' },
  { id: 4, rule: 'PCI-DSS Req 8 – Authentication', severity: 'Low', status: 'Open', detectedAt: '2024-03-10' },
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

export default function ComplianceCopilotDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Compliance Co-Pilot</h1>
        <p className="text-gray-500">Intelligent compliance monitoring and violation detection</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Bot className="w-5 h-5 text-blue-500" />} title="AI Scans Today" value="142" subtitle="Automated checks run" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-red-500" />} title="Open Violations" value="4" subtitle="Require attention" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-500" />} title="Compliance Score" value="94%" subtitle="Across all frameworks" />
        <StatCard icon={<BookOpen className="w-5 h-5 text-purple-500" />} title="Policies Tracked" value="38" subtitle="Active policy rules" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Violations</h2>
        <div className="space-y-3">
          {MOCK_VIOLATIONS.map((v) => (
            <div key={v.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                <div>
                  <p className="font-medium text-gray-900">{v.rule}</p>
                  <p className="text-sm text-gray-500">Detected {v.detectedAt} · {v.status}</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                v.severity === 'Critical' ? 'bg-red-100 text-red-700' :
                v.severity === 'High' ? 'bg-orange-100 text-orange-700' :
                v.severity === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {v.severity}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
