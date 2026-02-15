'use client'

import { useState } from 'react'
import { Shield, TrendingUp, Award, BarChart3, ArrowUp, ArrowDown, Minus } from 'lucide-react'
import { usePostureScore, usePostureBenchmark } from '@/hooks/useNextgenApi'
import type { PostureScore, DimensionDetail, PostureBenchmark } from '@/types/nextgen'

const MOCK_SCORE: PostureScore = {
  overall_score: 79.8,
  overall_grade: 'B',
  dimensions: [
    { dimension: 'Privacy & Data Protection', score: 77, max_score: 100, grade: 'C', findings_count: 3, critical_findings: 1, drivers: [{ driver: '1 critical finding(s) detected', impact: -5 }], trend: 'stable' },
    { dimension: 'Security Controls', score: 88, max_score: 100, grade: 'B', findings_count: 2, critical_findings: 0, drivers: [{ driver: 'Strong controls in place', impact: 0 }], trend: 'improving' },
    { dimension: 'Regulatory Alignment', score: 65, max_score: 100, grade: 'D', findings_count: 5, critical_findings: 2, drivers: [{ driver: '2 critical finding(s) detected', impact: -10 }], trend: 'degrading' },
    { dimension: 'Access Control', score: 91, max_score: 100, grade: 'A', findings_count: 1, critical_findings: 0, drivers: [{ driver: 'Strong controls in place', impact: 0 }], trend: 'improving' },
    { dimension: 'Incident Response', score: 62, max_score: 100, grade: 'D', findings_count: 4, critical_findings: 1, drivers: [{ driver: '1 critical finding(s) detected', impact: -5 }], trend: 'degrading' },
    { dimension: 'Vendor Management', score: 78, max_score: 100, grade: 'C', findings_count: 3, critical_findings: 0, drivers: [], trend: 'stable' },
    { dimension: 'Documentation', score: 85, max_score: 100, grade: 'B', findings_count: 2, critical_findings: 0, drivers: [{ driver: 'Strong controls in place', impact: 0 }], trend: 'improving' },
  ],
  calculated_at: new Date().toISOString(),
  repo: 'default',
  recommendations: [
    'Improve Incident Response: currently D (62%)',
    'Improve Regulatory Alignment: currently D (65%)',
    'Improve Privacy & Data Protection: currently C (77%)',
  ],
}

const MOCK_BENCHMARK: PostureBenchmark = {
  industry: 'saas',
  your_score: 79.8,
  industry_avg: 72.8,
  industry_median: 74.0,
  industry_p75: 80.0,
  industry_p90: 87.0,
  percentile: 72.5,
  peer_count: 2100,
  dimension_comparison: [],
}

const gradeColors: Record<string, string> = {
  A: 'text-green-600 bg-green-50 border-green-200',
  B: 'text-blue-600 bg-blue-50 border-blue-200',
  C: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  D: 'text-orange-600 bg-orange-50 border-orange-200',
  F: 'text-red-600 bg-red-50 border-red-200',
}

const trendIcons = {
  improving: <ArrowUp className="h-4 w-4 text-green-500" />,
  degrading: <ArrowDown className="h-4 w-4 text-red-500" />,
  stable: <Minus className="h-4 w-4 text-gray-400" />,
}

export default function PostureScoringDashboard() {
  const [industry, setIndustry] = useState('saas')
  const { data: liveScore } = usePostureScore()
  const { data: liveBenchmark } = usePostureBenchmark(industry)
  const score = liveScore || MOCK_SCORE
  const benchmark = liveBenchmark || MOCK_BENCHMARK

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Posture Scoring</h1>
        <p className="text-gray-500">7-dimension scoring with industry benchmarking and executive reporting</p>
      </div>

      {/* Overall Score */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Overall Score</p>
            <Shield className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{score.overall_score}%</p>
          <p className="mt-1"><span className={`px-2 py-0.5 text-sm font-bold rounded ${gradeColors[score.overall_grade]}`}>{score.overall_grade}</span></p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Industry Percentile</p>
            <TrendingUp className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{benchmark.percentile}th</p>
          <p className="mt-1 text-sm text-gray-500">vs {benchmark.peer_count} peers</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Industry Avg</p>
            <BarChart3 className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">{benchmark.industry_avg}%</p>
          <p className="mt-1 text-sm text-gray-500">You: +{(score.overall_score - benchmark.industry_avg).toFixed(1)}%</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Dimensions</p>
            <Award className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{score.dimensions.filter(d => d.grade === 'A' || d.grade === 'B').length}/7</p>
          <p className="mt-1 text-sm text-gray-500">At B or above</p>
        </div>
      </div>

      {/* Benchmark Selector */}
      <div className="card">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Industry Benchmark:</label>
          <select value={industry} onChange={e => setIndustry(e.target.value)} className="rounded-md border border-gray-300 px-3 py-2 text-sm">
            <option value="saas">SaaS</option>
            <option value="fintech">Fintech</option>
            <option value="healthtech">Healthtech</option>
            <option value="ecommerce">E-Commerce</option>
            <option value="ai_company">AI Companies</option>
          </select>
        </div>
      </div>

      {/* Dimensions */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Dimension Breakdown</h2>
        <div className="space-y-4">
          {score.dimensions.map((dim: DimensionDetail, i: number) => (
            <div key={i} className="flex items-center gap-4">
              <div className="w-44 flex items-center gap-2">
                {trendIcons[dim.trend as keyof typeof trendIcons] || trendIcons.stable}
                <span className="text-sm font-medium text-gray-700">{dim.dimension}</span>
              </div>
              <div className="flex-1">
                <div className="bg-gray-100 rounded-full h-4 relative">
                  <div
                    className={`h-4 rounded-full transition-all ${dim.score >= 80 ? 'bg-green-500' : dim.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${dim.score}%` }}
                  />
                </div>
              </div>
              <span className={`w-10 px-2 py-0.5 text-center text-xs font-bold rounded ${gradeColors[dim.grade]}`}>{dim.grade}</span>
              <span className="w-12 text-sm text-gray-600 text-right">{dim.score}%</span>
              {dim.critical_findings > 0 && (
                <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">{dim.critical_findings} critical</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      {score.recommendations.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Recommendations</h2>
          <ul className="space-y-2">
            {score.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="text-orange-500 mt-0.5">⚠</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
