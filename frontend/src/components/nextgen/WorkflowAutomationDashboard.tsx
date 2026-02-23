'use client'

import { Settings, Zap, Activity, CheckCircle } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Evidence Collection', detail: 'Auto-gather audit evidence', value: 'Active' },
  { id: 2, name: 'Control Testing', detail: 'Scheduled compliance checks', value: 'Active' },
  { id: 3, name: 'Report Generation', detail: 'Automated compliance reports', value: 'Active' },
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

export default function WorkflowAutomationDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Workflow Automation</h1>
        <p className="text-gray-500">Automated compliance workflow orchestration</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Settings className="h-5 w-5 text-blue-600" />} title="Workflows" value="42" subtitle="Active" />
        <StatCard icon={<Zap className="h-5 w-5 text-green-600" />} title="Executions" value="1.8K" subtitle="This month" />
        <StatCard icon={<Activity className="h-5 w-5 text-purple-600" />} title="Success Rate" value="97%" subtitle="Completion" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-orange-600" />} title="Time Saved" value="680h" subtitle="This quarter" />
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
