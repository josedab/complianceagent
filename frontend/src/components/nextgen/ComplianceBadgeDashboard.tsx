'use client'

import { Award, Eye, Code, TrendingUp } from 'lucide-react'

const MOCK_DATA = [
  { id: 1, name: 'complianceagent/backend', detail: 'SOC 2 + HIPAA — last scanned 2 hours ago', status: 'Score: 94/100' },
  { id: 2, name: 'complianceagent/frontend', detail: 'OWASP Top 10 — last scanned 5 hours ago', status: 'Score: 87/100' },
  { id: 3, name: 'complianceagent/infrastructure', detail: 'CIS Benchmarks — last scanned 1 day ago', status: 'Score: 72/100' },
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

export default function ComplianceBadgeDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Score Badge & Scorecard</h1>
        <p className="text-gray-500">Repository compliance scores, badge embeds, and trend tracking</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Award className="h-5 w-5 text-blue-600" />} title="Avg Score" value="84" subtitle="Across all repos" />
        <StatCard icon={<Eye className="h-5 w-5 text-green-600" />} title="Badge Views" value="1.2k" subtitle="Last 7 days" />
        <StatCard icon={<Code className="h-5 w-5 text-purple-600" />} title="Repos Tracked" value="3" subtitle="With active badges" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-orange-600" />} title="Trend" value="+6%" subtitle="Score improvement (30d)" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Repository Scorecards</h2>
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
