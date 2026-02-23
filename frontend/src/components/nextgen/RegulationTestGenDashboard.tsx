'use client'

import { FlaskConical, FileCode, CheckCircle, Zap } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'GDPR Test Suite', detail: 'Data protection test cases', value: '234 tests' },
  { id: 2, name: 'SOC 2 Validators', detail: 'Control verification tests', value: '186 tests' },
  { id: 3, name: 'HIPAA Checks', detail: 'Healthcare compliance tests', value: '142 tests' },
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

export default function RegulationTestGenDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulation Test Generator</h1>
        <p className="text-gray-500">Auto-generate compliance test cases from regulations</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FlaskConical className="h-5 w-5 text-blue-600" />} title="Tests" value="1.2K" subtitle="Total" />
        <StatCard icon={<FileCode className="h-5 w-5 text-green-600" />} title="Coverage" value="89%" subtitle="Regulation coverage" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-purple-600" />} title="Pass Rate" value="94%" subtitle="Current" />
        <StatCard icon={<Zap className="h-5 w-5 text-orange-600" />} title="Generated" value="48/day" subtitle="Avg generation" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Items</h2>
        <div className="space-y-3">
          {ITEMS.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail}</p>
              </div>
              <span className="text-sm text-gray-600">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
