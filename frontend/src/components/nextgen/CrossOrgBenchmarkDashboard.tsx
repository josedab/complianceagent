'use client'

import { BarChart3, Users, TrendingUp, Award } from 'lucide-react'

const MOCK_BENCHMARKS = [
  { industry: 'Fintech', avg: 82.5, yours: 87.0, percentile: 72, peers: 340 },
  { industry: 'Healthtech', avg: 78.0, yours: 85.0, percentile: 81, peers: 210 },
  { industry: 'SaaS', avg: 76.0, yours: 87.0, percentile: 88, peers: 520 },
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

export default function CrossOrgBenchmarkDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cross-Organization Benchmarking</h1>
        <p className="text-gray-500">Anonymous peer comparison with differential privacy</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<BarChart3 className="h-5 w-5 text-blue-600" />} title="Your Score" value="87.0" subtitle="Overall compliance" />
        <StatCard icon={<Users className="h-5 w-5 text-green-600" />} title="Participants" value="1,070" subtitle="Total orgs" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-purple-600" />} title="Percentile" value="80th" subtitle="Among peers" />
        <StatCard icon={<Award className="h-5 w-5 text-orange-600" />} title="Industries" value="8" subtitle="Benchmarked" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Industry Comparison</h2>
        <div className="space-y-3">
          {MOCK_BENCHMARKS.map((b) => (
            <div key={b.industry} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{b.industry}</span>
                <p className="text-xs text-gray-500">{b.peers} peers · avg {b.avg}%</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-semibold text-green-600">{b.percentile}th percentile</span>
                <p className="text-xs text-gray-500">Your: {b.yours}%</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
