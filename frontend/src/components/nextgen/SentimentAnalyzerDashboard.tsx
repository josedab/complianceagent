'use client'

import { TrendingUp, Flame, BarChart3, Target } from 'lucide-react'
import { useRegulatoryHeatmap } from '@/hooks/useNextgenApi'
import type { RiskHeatmapCellRecord } from '@/types/nextgen'

interface HeatmapDisplay extends RiskHeatmapCellRecord {
  id: string;
  category: string;
  enforcement_trend: string;
  avg_fine_millions: number;
  sentiment: string;
}

const MOCK_HEATMAP: HeatmapDisplay[] = [
  { id: 'rh1', regulation: 'GDPR', jurisdiction: 'EU', risk_score: 8.5, trend: 'increasing', color: 'red', category: 'Data Protection', enforcement_trend: 'increasing', avg_fine_millions: 12.4, sentiment: 'negative' },
  { id: 'rh2', regulation: 'SOC 2', jurisdiction: 'US', risk_score: 6.2, trend: 'stable', color: 'yellow', category: 'Security Controls', enforcement_trend: 'stable', avg_fine_millions: 5.1, sentiment: 'neutral' },
  { id: 'rh3', regulation: 'HIPAA', jurisdiction: 'US', risk_score: 7.8, trend: 'increasing', color: 'orange', category: 'Health Data', enforcement_trend: 'increasing', avg_fine_millions: 8.9, sentiment: 'negative' },
  { id: 'rh4', regulation: 'PCI DSS', jurisdiction: 'Global', risk_score: 5.4, trend: 'decreasing', color: 'green', category: 'Payment Security', enforcement_trend: 'decreasing', avg_fine_millions: 3.2, sentiment: 'positive' },
  { id: 'rh5', regulation: 'EU AI Act', jurisdiction: 'EU', risk_score: 9.1, trend: 'increasing', color: 'red', category: 'AI Governance', enforcement_trend: 'increasing', avg_fine_millions: 15.0, sentiment: 'negative' },
  { id: 'rh6', regulation: 'CCPA', jurisdiction: 'California', risk_score: 6.8, trend: 'stable', color: 'yellow', category: 'Privacy', enforcement_trend: 'stable', avg_fine_millions: 4.5, sentiment: 'neutral' },
]

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
  const { data: liveHeatmap } = useRegulatoryHeatmap()

  const heatmap = (liveHeatmap as HeatmapDisplay[] | null) || MOCK_HEATMAP
  const highRisk = heatmap.filter(h => h.risk_score >= 7).length
  const avgFine = (heatmap.reduce((sum, h) => sum + h.avg_fine_millions, 0) / heatmap.length).toFixed(1)
  const increasingCount = heatmap.filter(h => h.enforcement_trend === 'increasing').length
  const trendPct = ((increasingCount / heatmap.length) * 100).toFixed(0)

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
          <p className="mt-2 text-3xl font-bold text-gray-900">{heatmap.length}</p>
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
            <p className="text-sm font-medium text-gray-500">Avg Fine</p>
            <BarChart3 className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">${avgFine}M</p>
          <p className="mt-1 text-sm text-gray-500">Average enforcement</p>
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {heatmap.map(cell => (
            <div key={cell.id} className={`p-4 rounded-lg border ${cellColors[cell.color] || cellColors.yellow}`}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900">{cell.regulation}</span>
                <span className="text-lg font-bold">{cell.risk_score}</span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{cell.category}</p>
              <div className="flex items-center gap-3 text-sm text-gray-500">
                <span>Fine: ${cell.avg_fine_millions}M</span>
                <span>{trendIcons[cell.enforcement_trend]} {cell.enforcement_trend}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
