'use client'

import { useState } from 'react'
import { TrendingUp, AlertCircle, Clock, Globe, BarChart3, ChevronRight, Eye } from 'lucide-react'

type ConfidenceLevel = 'very_high' | 'high' | 'medium' | 'low' | 'very_low'
type PredictionStatus = 'draft' | 'proposed' | 'committee' | 'enacted' | 'effective'

interface Prediction {
  id: string
  title: string
  jurisdiction: string
  framework: string
  confidence: ConfidenceLevel
  probability: number
  predicted_date: string
  status: PredictionStatus
  impact_score: number
  description: string
  affected_sectors: string[]
}

const confidenceConfig: Record<ConfidenceLevel, { label: string; color: string; bg: string }> = {
  very_high: { label: 'Very High', color: 'text-green-700', bg: 'bg-green-100' },
  high: { label: 'High', color: 'text-blue-700', bg: 'bg-blue-100' },
  medium: { label: 'Medium', color: 'text-yellow-700', bg: 'bg-yellow-100' },
  low: { label: 'Low', color: 'text-orange-700', bg: 'bg-orange-100' },
  very_low: { label: 'Very Low', color: 'text-red-700', bg: 'bg-red-100' },
}

const statusConfig: Record<PredictionStatus, { label: string; color: string }> = {
  draft: { label: 'Draft', color: 'text-gray-600 bg-gray-100' },
  proposed: { label: 'Proposed', color: 'text-blue-600 bg-blue-100' },
  committee: { label: 'In Committee', color: 'text-purple-600 bg-purple-100' },
  enacted: { label: 'Enacted', color: 'text-green-600 bg-green-100' },
  effective: { label: 'Effective', color: 'text-indigo-600 bg-indigo-100' },
}

const MOCK_PREDICTIONS: Prediction[] = [
  {
    id: 'p1', title: 'US Federal Privacy Act (ADPPA Successor)', jurisdiction: 'US Federal',
    framework: 'privacy', confidence: 'high', probability: 0.78, predicted_date: '2026-09-01',
    status: 'committee', impact_score: 9.2, description: 'Comprehensive federal privacy law replacing state patchwork. Would establish uniform consent, data minimization, and breach notification standards.',
    affected_sectors: ['Technology', 'Healthcare', 'Finance', 'Retail'],
  },
  {
    id: 'p2', title: 'EU AI Act Enforcement Guidance', jurisdiction: 'EU',
    framework: 'ai_governance', confidence: 'very_high', probability: 0.95, predicted_date: '2026-06-15',
    status: 'proposed', impact_score: 8.8, description: 'Detailed enforcement guidance for high-risk AI systems. Will specify technical documentation, conformity assessment, and post-market monitoring requirements.',
    affected_sectors: ['AI/ML', 'Healthcare', 'Finance', 'HR Tech'],
  },
  {
    id: 'p3', title: 'California AI Transparency Act', jurisdiction: 'California',
    framework: 'ai_governance', confidence: 'medium', probability: 0.62, predicted_date: '2026-11-01',
    status: 'draft', impact_score: 7.5, description: 'Requires disclosure when AI is used in consequential decisions. Mandates algorithmic impact assessments for systems affecting employment, credit, and housing.',
    affected_sectors: ['AI/ML', 'HR Tech', 'Finance'],
  },
  {
    id: 'p4', title: 'APAC Data Sovereignty Framework', jurisdiction: 'APAC',
    framework: 'privacy', confidence: 'medium', probability: 0.55, predicted_date: '2027-03-01',
    status: 'draft', impact_score: 7.0, description: 'Harmonized data sovereignty standards for ASEAN nations. Would create mutual recognition framework for cross-border data transfers.',
    affected_sectors: ['Technology', 'Finance', 'E-commerce'],
  },
  {
    id: 'p5', title: 'UK Online Safety Act Amendment', jurisdiction: 'UK',
    framework: 'content_safety', confidence: 'high', probability: 0.82, predicted_date: '2026-08-01',
    status: 'proposed', impact_score: 6.5, description: 'Extends age verification requirements to AI chatbots and generative AI services. Adds mandatory content moderation reporting.',
    affected_sectors: ['Social Media', 'AI/ML', 'Gaming'],
  },
  {
    id: 'p6', title: 'SEC Cybersecurity Disclosure Rule Update', jurisdiction: 'US Federal',
    framework: 'security', confidence: 'high', probability: 0.85, predicted_date: '2026-07-01',
    status: 'committee', impact_score: 8.0, description: 'Expands material cybersecurity incident reporting to include supply chain breaches and third-party vendor incidents.',
    affected_sectors: ['Finance', 'Technology', 'Healthcare'],
  },
]

export default function PredictionsDashboard() {
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string>('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const jurisdictions = ['all', ...Array.from(new Set(MOCK_PREDICTIONS.map(p => p.jurisdiction)))]

  const filtered = selectedJurisdiction === 'all'
    ? MOCK_PREDICTIONS
    : MOCK_PREDICTIONS.filter(p => p.jurisdiction === selectedJurisdiction)

  const avgConfidence = filtered.reduce((acc, p) => acc + p.probability, 0) / filtered.length
  const highImpact = filtered.filter(p => p.impact_score >= 8).length
  const next6mo = filtered.filter(p => {
    const d = new Date(p.predicted_date)
    const now = new Date()
    const sixMonths = new Date(now.getFullYear(), now.getMonth() + 6, now.getDate())
    return d <= sixMonths
  }).length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <TrendingUp className="h-6 w-6 text-indigo-600" />
          Regulatory Predictions
        </h1>
        <p className="text-gray-500">AI-powered forecasting of upcoming regulatory changes</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Active Predictions</p>
            <Eye className="h-5 w-5 text-indigo-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{filtered.length}</p>
          <p className="mt-1 text-sm text-gray-500">Across {new Set(filtered.map(p => p.jurisdiction)).size} jurisdictions</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Avg Confidence</p>
            <BarChart3 className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{(avgConfidence * 100).toFixed(0)}%</p>
          <p className="mt-1 text-sm text-gray-500">Prediction accuracy</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">High Impact</p>
            <AlertCircle className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{highImpact}</p>
          <p className="mt-1 text-sm text-gray-500">Score ≥ 8.0</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Next 6 Months</p>
            <Clock className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{next6mo}</p>
          <p className="mt-1 text-sm text-gray-500">Expected to materialize</p>
        </div>
      </div>

      {/* Jurisdiction Filter */}
      <div className="flex items-center gap-2">
        <Globe className="h-4 w-4 text-gray-400" />
        <div className="flex gap-2">
          {jurisdictions.map(j => (
            <button
              key={j}
              onClick={() => setSelectedJurisdiction(j)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium ${
                selectedJurisdiction === j
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {j === 'all' ? 'All Jurisdictions' : j}
            </button>
          ))}
        </div>
      </div>

      {/* Prediction Cards */}
      <div className="space-y-3">
        {filtered.sort((a, b) => b.impact_score - a.impact_score).map(prediction => {
          const cc = confidenceConfig[prediction.confidence]
          const sc = statusConfig[prediction.status]
          const isExpanded = expandedId === prediction.id
          const daysUntil = Math.ceil((new Date(prediction.predicted_date).getTime() - Date.now()) / 86400000)

          return (
            <div key={prediction.id} className="card">
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpandedId(isExpanded ? null : prediction.id)}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${sc.color}`}>{sc.label}</span>
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${cc.bg} ${cc.color}`}>{(prediction.probability * 100).toFixed(0)}% likely</span>
                    <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">{prediction.jurisdiction}</span>
                  </div>
                  <h3 className="font-semibold text-gray-900">{prediction.title}</h3>
                  <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                    <span>Impact: <span className={`font-bold ${prediction.impact_score >= 8 ? 'text-red-600' : 'text-orange-600'}`}>{prediction.impact_score}/10</span></span>
                    <span>{daysUntil > 0 ? `${daysUntil} days away` : 'Overdue'}</span>
                    <span>Target: {new Date(prediction.predicted_date).toLocaleDateString()}</span>
                  </div>
                </div>
                <ChevronRight className={`h-5 w-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              </div>

              {isExpanded && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-700 mb-3">{prediction.description}</p>
                  <div className="flex flex-wrap gap-2 mb-3">
                    <span className="text-xs text-gray-500 mr-1">Affected sectors:</span>
                    {prediction.affected_sectors.map(s => (
                      <span key={s} className="px-2 py-0.5 bg-indigo-50 text-indigo-700 text-xs rounded-full">{s}</span>
                    ))}
                  </div>
                  {/* Probability Bar */}
                  <div>
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Probability</span>
                      <span>{(prediction.probability * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${prediction.probability >= 0.8 ? 'bg-green-500' : prediction.probability >= 0.6 ? 'bg-yellow-500' : 'bg-orange-500'}`}
                        style={{ width: `${prediction.probability * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
