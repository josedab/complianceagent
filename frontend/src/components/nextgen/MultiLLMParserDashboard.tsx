'use client'

import { Brain, Cpu, Layers, Zap } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'GPT-4 Parser', detail: 'Primary regulation parser', value: '96% accuracy' },
  { id: 2, name: 'Claude Parser', detail: 'Secondary validation', value: '97% accuracy' },
  { id: 3, name: 'Gemini Parser', detail: 'Cross-validation engine', value: '94% accuracy' },
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

export default function MultiLLMParserDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Multi-LLM Parser</h1>
        <p className="text-gray-500">Parse regulations using multiple LLM providers</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Brain className="h-5 w-5 text-blue-600" />} title="Models" value="6" subtitle="Active" />
        <StatCard icon={<Cpu className="h-5 w-5 text-green-600" />} title="Parsed" value="4.5K" subtitle="Documents" />
        <StatCard icon={<Layers className="h-5 w-5 text-purple-600" />} title="Accuracy" value="97%" subtitle="Consensus accuracy" />
        <StatCard icon={<Zap className="h-5 w-5 text-orange-600" />} title="Cost" value="$0.02" subtitle="Per document" />
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
