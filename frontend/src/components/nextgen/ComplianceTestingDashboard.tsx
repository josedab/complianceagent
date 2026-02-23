'use client'

import { FlaskConical, CheckCircle, AlertTriangle, Shuffle } from 'lucide-react'

const TEST_SUITES = [
  { id: 1, name: 'Regulatory Compliance', detail: '42 test cases', status: 'Passed' },
  { id: 2, name: 'Data Privacy', detail: '28 test cases', status: 'Passed' },
  { id: 3, name: 'Access Control', detail: '35 test cases', status: 'Warning' },
  { id: 4, name: 'Audit Trail', detail: '19 test cases', status: 'Passed' },
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

export default function ComplianceTestingDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Testing Framework</h1>
        <p className="text-gray-500">Automated compliance test suites and results</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FlaskConical className="h-5 w-5 text-blue-600" />} title="Test Suites" value="4" subtitle="Total suites" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-green-600" />} title="Passed" value="124" subtitle="Test cases" />
        <StatCard icon={<AlertTriangle className="h-5 w-5 text-purple-600" />} title="Warnings" value="3" subtitle="Needs review" />
        <StatCard icon={<Shuffle className="h-5 w-5 text-orange-600" />} title="Coverage" value="94%" subtitle="Rule coverage" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Test Suites</h2>
        <div className="space-y-3">
          {TEST_SUITES.map((item) => (
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
