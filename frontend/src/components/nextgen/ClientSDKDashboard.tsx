'use client'

import { Package, Code, Terminal, Download } from 'lucide-react'

const MOCK_DATA = [
  { id: 1, name: '@compliance-agent/sdk-python', detail: 'v2.4.1 — Policy-as-code bindings, async support', status: '12.3k downloads' },
  { id: 2, name: '@compliance-agent/sdk-node', detail: 'v3.1.0 — TypeScript-first, ESM & CJS', status: '8.7k downloads' },
  { id: 3, name: '@compliance-agent/sdk-go', detail: 'v1.2.0 — gRPC client, context-aware scanning', status: '4.1k downloads' },
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

export default function ClientSDKDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Agent SDK</h1>
        <p className="text-gray-500">Client libraries, package versions, and download metrics</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Package className="h-5 w-5 text-blue-600" />} title="Packages" value="3" subtitle="Published SDKs" />
        <StatCard icon={<Code className="h-5 w-5 text-green-600" />} title="Languages" value="3" subtitle="Python, Node, Go" />
        <StatCard icon={<Terminal className="h-5 w-5 text-purple-600" />} title="API Coverage" value="94%" subtitle="Endpoints supported" />
        <StatCard icon={<Download className="h-5 w-5 text-orange-600" />} title="Total Downloads" value="25.1k" subtitle="Last 30 days" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">SDK Packages</h2>
        <div className="space-y-3">
          {MOCK_DATA.map((item) => (
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
