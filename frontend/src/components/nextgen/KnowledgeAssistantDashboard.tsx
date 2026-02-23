'use client'

import { Brain, Send, FileText, Search } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Policy Lookup', detail: 'Find relevant compliance policies', value: '1.2K uses' },
  { id: 2, name: 'Regulation Q&A', detail: 'Answer regulatory questions', value: '890 uses' },
  { id: 3, name: 'Control Advisor', detail: 'Recommend applicable controls', value: '567 uses' },
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

export default function KnowledgeAssistantDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Knowledge Assistant</h1>
        <p className="text-gray-500">AI-powered compliance knowledge assistant</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Brain className="h-5 w-5 text-blue-600" />} title="Queries" value="4.2K" subtitle="Answered" />
        <StatCard icon={<Send className="h-5 w-5 text-green-600" />} title="Accuracy" value="96%" subtitle="Confidence" />
        <StatCard icon={<FileText className="h-5 w-5 text-purple-600" />} title="Sources" value="1.8K" subtitle="Indexed" />
        <StatCard icon={<Search className="h-5 w-5 text-orange-600" />} title="Response" value="0.8s" subtitle="Avg time" />
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
