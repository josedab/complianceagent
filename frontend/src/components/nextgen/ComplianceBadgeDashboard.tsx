'use client'

import { Award, CheckCircle, TrendingUp, Shield } from 'lucide-react'
import { useReferenceRepos } from '@/hooks/useNextgenApi'

export default function ComplianceBadgeDashboard() {
  const { data: repos, loading, error, refetch } = useReferenceRepos()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Badge</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Badge</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Compliance Badge: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Badge</h1>
        <p className="text-gray-500">Certify repositories with compliance badges and scorecards</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-2 mb-2"><Award className="w-5 h-5 text-yellow-500" /><span className="text-sm text-gray-500">Badged Repos</span></div>
          <p className="text-2xl font-bold text-gray-900">{repos?.length ?? 0}</p>
          <p className="text-xs text-gray-500 mt-1">Reference repositories</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-2 mb-2"><CheckCircle className="w-5 h-5 text-green-500" /><span className="text-sm text-gray-500">Verified</span></div>
          <p className="text-2xl font-bold text-gray-900">{repos?.filter(r => r.verified).length ?? 0}</p>
          <p className="text-xs text-gray-500 mt-1">Verified references</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-2 mb-2"><TrendingUp className="w-5 h-5 text-blue-500" /><span className="text-sm text-gray-500">Avg Score</span></div>
          <p className="text-2xl font-bold text-gray-900">
            {repos && repos.length > 0 ? `${(repos.reduce((s, r) => s + r.compliance_score, 0) / repos.length).toFixed(1)}%` : '—'}
          </p>
          <p className="text-xs text-gray-500 mt-1">Compliance score</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-2 mb-2"><Shield className="w-5 h-5 text-purple-500" /><span className="text-sm text-gray-500">Frameworks</span></div>
          <p className="text-2xl font-bold text-gray-900">
            {repos ? new Set(repos.flatMap(r => r.frameworks)).size : 0}
          </p>
          <p className="text-xs text-gray-500 mt-1">Unique frameworks</p>
        </div>
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Repository Badges</h2>
        {!repos || repos.length === 0 ? (
          <p className="text-gray-500">No badged repositories yet.</p>
        ) : (
          <div className="space-y-3">
            {repos.map((repo) => (
              <div key={repo.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Award className="w-5 h-5 text-yellow-500" />
                  <div>
                    <p className="font-medium text-gray-900">{repo.name}</p>
                    <p className="text-sm text-gray-500">Frameworks: {repo.frameworks.join(', ')} · Score: {repo.compliance_score.toFixed(1)}%</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${repo.verified ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                  {repo.verified ? 'Verified' : 'Unverified'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
