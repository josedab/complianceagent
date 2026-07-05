'use client'

import { Target, BarChart3, TrendingUp, Award } from 'lucide-react'
import { usePostureScore, usePostureBenchmark, usePostureHistory } from '@/hooks/useNextgenApi'

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

function ordinalSuffix(n: number): string {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return s[(v - 20) % 10] || s[v] || s[0]
}

export default function PostureScoringDashboard() {
  const { data: score, loading: scoreLoading, error: scoreError, refetch: refetchScore } = usePostureScore()
  const { data: benchmark, loading: benchmarkLoading, error: benchmarkError } = usePostureBenchmark('technology')
  const { data: history, loading: historyLoading } = usePostureHistory()

  const loading = scoreLoading || benchmarkLoading || historyLoading
  const error = scoreError || benchmarkError

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}
        </div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Posture Scoring</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading posture score: {error.message}</p>
          <button onClick={refetchScore} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const dimensions = score?.dimensions || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Posture Scoring</h1>
        <p className="text-gray-500">Continuous compliance posture scoring and benchmarking</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Target className="h-5 w-5 text-blue-600" />} title="Score" value={score ? `${score.overall_score}%` : 'N/A'} subtitle={score ? `Grade ${score.overall_grade}` : 'Current posture'} />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-green-600" />} title="Dimensions" value={String(dimensions.length)} subtitle="Evaluated" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-purple-600" />} title="Trend" value={history?.trend || 'N/A'} subtitle={history ? `${history.improvement_rate > 0 ? '+' : ''}${history.improvement_rate}% rate` : 'Month over month'} />
        <StatCard icon={<Award className="h-5 w-5 text-orange-600" />} title="Percentile" value={benchmark ? `${benchmark.percentile}${ordinalSuffix(benchmark.percentile)}` : 'N/A'} subtitle={`vs ${benchmark?.industry || 'industry'}`} />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Dimension Breakdown</h2>
        {dimensions.length === 0 ? (
          <p className="text-gray-500 text-sm">No dimension data available.</p>
        ) : (
          <div className="space-y-3">
            {dimensions.map((d) => (
              <div key={d.dimension} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
                <div>
                  <span className="font-medium text-gray-900">{d.dimension}</span>
                  <p className="text-xs text-gray-500">{d.findings_count} findings ({d.critical_findings} critical) · trend {d.trend}</p>
                </div>
                <span className="text-sm text-gray-600">{d.score}/{d.max_score} ({d.grade})</span>
              </div>
            ))}
          </div>
        )}
      </div>
      {score && score.recommendations.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h2>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
            {score.recommendations.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}
    </div>
  )
}
