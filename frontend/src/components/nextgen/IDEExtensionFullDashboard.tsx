'use client'

import { Code, Shield, Zap, FileCode } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'VS Code Extension', detail: 'Primary IDE integration', value: 'v3.2.1' },
  { id: 2, name: 'JetBrains Plugin', detail: 'IntelliJ IDEA support', value: 'v2.1.0' },
  { id: 3, name: 'Neovim Plugin', detail: 'Terminal IDE support', value: 'v1.4.2' },
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

export default function IDEExtensionFullDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">IDE Compliance Extension</h1>
        <p className="text-gray-500">Full-featured IDE extension for compliance development</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Code className="h-5 w-5 text-blue-600" />} title="Installs" value="2.8K" subtitle="Active" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Scans/Day" value="14K" subtitle="Average" />
        <StatCard icon={<Zap className="h-5 w-5 text-purple-600" />} title="Fix Rate" value="94%" subtitle="Auto-fix success" />
        <StatCard icon={<FileCode className="h-5 w-5 text-orange-600" />} title="Languages" value="12" subtitle="Supported" />
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
