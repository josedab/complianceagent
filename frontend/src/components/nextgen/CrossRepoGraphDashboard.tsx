'use client'

import { GitBranch, Shield, AlertTriangle, BarChart3 } from 'lucide-react'

const MOCK_REPOS = [
  { repo: 'org/api-service', score: 88.0, deps: 3, violations: 2, status: 'healthy' },
  { repo: 'org/web-app', score: 91.5, deps: 2, violations: 0, status: 'healthy' },
  { repo: 'org/data-pipeline', score: 76.0, deps: 5, violations: 8, status: 'at-risk' },
  { repo: 'org/auth-service', score: 94.0, deps: 1, violations: 0, status: 'healthy' },
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

export default function CrossRepoGraphDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cross-Repository Compliance Graph</h1>
        <p className="text-gray-500">Organization-wide compliance with dependency tracking</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<GitBranch className="h-5 w-5 text-blue-600" />} title="Repositories" value={String(MOCK_REPOS.length)} subtitle="Tracked repos" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Avg Score" value="87.4%" subtitle="Across all repos" />
        <StatCard icon={<AlertTriangle className="h-5 w-5 text-orange-600" />} title="Violations" value="10" subtitle="Total open" />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-purple-600" />} title="Dependencies" value="11" subtitle="Cross-repo links" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Repository Compliance</h2>
        <div className="space-y-3">
          {MOCK_REPOS.map((r) => (
            <div key={r.repo} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{r.repo}</span>
                <p className="text-xs text-gray-500">{r.deps} deps · {r.violations} violations</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-900">{r.score}%</span>
                <span className={`px-2 py-0.5 text-xs rounded ${r.status === 'healthy' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>{r.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
