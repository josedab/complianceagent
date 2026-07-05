'use client'

import { GitPullRequest, CheckCircle, AlertTriangle, Clock } from 'lucide-react'
import { useCodeReviews, useCodeReviewStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function CodeReviewAgentDashboard() {
  const { data: reviews, loading: reviewsLoading, error: reviewsError, refetch } = useCodeReviews()
  const { data: stats, loading: statsLoading, error: statsError } = useCodeReviewStats()

  const loading = reviewsLoading || statsLoading
  const error = reviewsError || statsError

  const s = stats as Record<string, unknown> | null

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Code Review Agent</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Code Review Agent</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Code Review Agent: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Code Review Agent</h1>
        <p className="text-gray-500">Automated compliance review for pull requests</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<GitPullRequest className="w-5 h-5 text-blue-500" />} title="Total Reviews" value={String(s?.total_reviews ?? 0)} subtitle="PRs analyzed" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-500" />} title="Auto Approved" value={String(s?.auto_approved ?? 0)} subtitle="Low-risk PRs" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-orange-500" />} title="Suggestions" value={String(s?.suggestions_made ?? 0)} subtitle={`${((Number(s?.acceptance_rate ?? 0)) * 100).toFixed(1)}% accepted`} />
        <StatCard icon={<Clock className="w-5 h-5 text-purple-500" />} title="Avg Review" value={`${(Number(s?.avg_review_time_ms ?? 0) / 1000).toFixed(1)}s`} subtitle="Time per PR" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Reviews</h2>
        {!reviews || reviews.length === 0 ? (
          <p className="text-gray-500">No code reviews yet.</p>
        ) : (
          <div className="space-y-3">
            {reviews.slice(0, 10).map((review, idx) => {
              const r = review as Record<string, unknown>
              return (
                <div key={String(r.id ?? idx)} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <GitPullRequest className="w-5 h-5 text-blue-500" />
                    <div>
                      <p className="font-medium text-gray-900">{String(r.repo ?? '')} #{String(r.pr_number ?? '')}</p>
                      <p className="text-sm text-gray-500">Risk: {String(r.overall_risk ?? '')} · {String(r.files_analyzed ?? 0)} files analyzed</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    r.decision === 'approve' ? 'bg-green-100 text-green-700' :
                    r.decision === 'request_changes' ? 'bg-red-100 text-red-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>{String(r.decision ?? '')}</span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
