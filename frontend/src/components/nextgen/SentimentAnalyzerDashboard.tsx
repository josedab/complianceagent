'use client'

import { TrendingUp, Flame, BarChart3, Target } from 'lucide-react'
import { useRegulatoryHeatmap } from '@/hooks/useNextgenApi'
import type { RiskHeatmapCellRecord } from '@/types/nextgen'

const cellColors: Record<string, string> = {
  red: 'bg-red-100 border-red-300',
  orange: 'bg-orange-100 border-orange-300',
  yellow: 'bg-yellow-100 border-yellow-300',
  green: 'bg-green-100 border-green-300',
}

const trendIcons: Record<string, string> = {
  increasing: '↑',
  stable: '→',
  decreasing: '↓',
}

export default function SentimentAnalyzerDashboard() {
  const { data: heatmap, loading, error, refetch } = useRegulatoryHeatmap()

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
        </div>
        <div className="card h-64 animate-pulse bg-gray-100" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading Regulatory Sentiment Analyzer: {error.message}</p>
        <button onClick={refetch} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const cells = heatmap ?? []
  const highRisk = cells.filter(h => h.risk_score >= 7).length
  const increasingCount = cells.filter(h => h.trend === 'increasing').length
  const trendPct = cells.length > 0 ? ((increasingCount / cells.length) * 100).toFixed(0) : '0'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Change Sentiment Analyzer</h1>
        <p className="text-gray-500">Predict enforcement priorities and optimize compliance spending</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Regulations Analyzed</p>
            <TrendingUp className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{cells.length}</p>
          <p className="mt-1 text-sm text-gray-500">Active monitoring</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">High Risk</p>
            <Flame className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{highRisk}</p>
          <p className="mt-1 text-sm text-red-500">Score ≥ 7.0</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Increasing Trend</p>
            <BarChart3 className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{increasingCount}</p>
          <p className="mt-1 text-sm text-gray-500">Rising enforcement</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Enforcement Trend</p>
            <Target className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">↑ {trendPct}%</p>
          <p className="mt-1 text-sm text-gray-500">Increasing enforcement</p>
        </div>
      </div>

      {/* Risk Heatmap */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Flame className="h-5 w-5 text-red-500" />
          <h2 className="text-lg font-semibold text-gray-900">Risk Heatmap</h2>
        </div>
        {cells.length === 0 ? (
          <p className="text-gray-500 text-sm">No heatmap data available yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {cells.map((cell: RiskHeatmapCellRecord, i: number) => (
              <div key={`${cell.regulation}-${cell.jurisdiction}-${i}`} className={`p-4 rounded-lg border ${cellColors[cell.color] || cellColors.yellow}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">{cell.regulation}</span>
                  <span className="text-lg font-bold">{cell.risk_score}</span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{cell.jurisdiction}</p>
                <div className="flex items-center gap-3 text-sm text-gray-500">
                  <span>{trendIcons[cell.trend] ?? '→'} {cell.trend}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
