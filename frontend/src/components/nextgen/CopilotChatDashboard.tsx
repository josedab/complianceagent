'use client'

import { Send, Brain, Activity, Users } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Policy Interpretation', detail: 'GDPR Article 17 analysis', value: 'Resolved' },
  { id: 2, name: 'Control Mapping', detail: 'SOC 2 to ISO mapping', value: 'Resolved' },
  { id: 3, name: 'Risk Assessment', detail: 'Third-party vendor query', value: 'Pending' },
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

export default function CopilotChatDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Copilot Chat</h1>
        <p className="text-gray-500">AI-powered compliance assistant for natural language queries</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Send className="h-5 w-5 text-blue-600" />} title="Queries" value="1.8K" subtitle="This week" />
        <StatCard icon={<Brain className="h-5 w-5 text-green-600" />} title="Accuracy" value="94%" subtitle="Answer accuracy" />
        <StatCard icon={<Activity className="h-5 w-5 text-purple-600" />} title="Avg Response" value="1.2s" subtitle="Response time" />
        <StatCard icon={<Users className="h-5 w-5 text-orange-600" />} title="Users" value="86" subtitle="Active" />
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
