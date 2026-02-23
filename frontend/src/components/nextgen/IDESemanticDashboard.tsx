'use client'

import { Brain, Code, Search, Cpu } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Data Flow Analysis', detail: 'Track PII through codebase', value: 'Active' },
  { id: 2, name: 'Access Pattern Detection', detail: 'RBAC compliance check', value: 'Active' },
  { id: 3, name: 'Crypto Usage Audit', detail: 'Encryption standard validation', value: 'Active' },
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

export default function IDESemanticDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">IDE Semantic Analysis</h1>
        <p className="text-gray-500">Semantic code analysis for compliance within IDEs</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Brain className="h-5 w-5 text-blue-600" />} title="Analyses" value="5.6K" subtitle="Completed" />
        <StatCard icon={<Code className="h-5 w-5 text-green-600" />} title="Patterns" value="234" subtitle="Detected" />
        <StatCard icon={<Search className="h-5 w-5 text-purple-600" />} title="Accuracy" value="96%" subtitle="Detection rate" />
        <StatCard icon={<Cpu className="h-5 w-5 text-orange-600" />} title="Speed" value="120ms" subtitle="Avg analysis" />
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
