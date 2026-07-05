'use client'

import { Brain, Eye, AlertTriangle, Shield } from 'lucide-react'
import { useAIModels, useAIObservatoryDashboard } from '@/hooks/useNextgenApi'
import type { AIModelRecord } from '@/types/nextgen'

const riskBadge: Record<string, { bg: string; text: string }> = {
  prohibited: { bg: 'bg-red-100', text: 'text-red-700' },
  high_risk: { bg: 'bg-orange-100', text: 'text-orange-700' },
  limited_risk: { bg: 'bg-yellow-100', text: 'text-yellow-700' },
  minimal_risk: { bg: 'bg-green-100', text: 'text-green-700' },
}

export default function AIObservatoryDashboard() {
  const { data: models, loading: modelsLoading, error: modelsError, refetch: refetchModels } = useAIModels()
  const { data: dashboard, loading: dashLoading, error: dashError, refetch: refetchDash } = useAIObservatoryDashboard()

  const loading = modelsLoading || dashLoading
  const error = modelsError || dashError

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
        <p className="text-red-800">Error loading AI Observatory: {error.message}</p>
        <button onClick={() => { refetchModels(); refetchDash(); }} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const highRisk = dashboard
    ? ((dashboard.by_risk_level['high_risk'] ?? 0) + (dashboard.by_risk_level['prohibited'] ?? 0))
    : 0
  const compliant = dashboard?.compliant_count ?? 0
  const avgBias = dashboard?.avg_bias_score != null ? dashboard.avg_bias_score.toFixed(2) : '—'
  const totalModels = dashboard?.total_models ?? models?.length ?? 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Model Compliance Observatory</h1>
        <p className="text-gray-500">EU AI Act risk classification, bias monitoring, and MLOps compliance</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Models Tracked</p>
            <Brain className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{totalModels}</p>
          <p className="mt-1 text-sm text-gray-500">In production</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">High-Risk</p>
            <AlertTriangle className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{highRisk}</p>
          <p className="mt-1 text-sm text-gray-500">Require oversight</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Compliant</p>
            <Shield className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{compliant}</p>
          <p className="mt-1 text-sm text-gray-500">Passing all checks</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Avg Bias Score</p>
            <Eye className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">{avgBias}</p>
          <p className="mt-1 text-sm text-gray-500">1.0 = no bias detected</p>
        </div>
      </div>

      {/* Model Cards */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="h-5 w-5 text-purple-500" />
          <h2 className="text-lg font-semibold text-gray-900">AI Models</h2>
        </div>
        {!models || models.length === 0 ? (
          <p className="text-gray-500 text-sm">No AI models registered yet.</p>
        ) : (
          <div className="space-y-3">
            {models.map((model: AIModelRecord) => {
              const badge = riskBadge[model.risk_level] ?? riskBadge.minimal_risk
              const isCompliant = model.status === 'compliant'
              return (
                <div key={model.id} className={`p-4 rounded-lg border ${isCompliant ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{model.name}</span>
                      <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${badge.bg} ${badge.text}`}>{model.risk_level.replace(/_/g, ' ')}</span>
                    </div>
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${isCompliant ? 'text-green-700 bg-white' : 'text-red-700 bg-white'}`}>
                      {isCompliant ? 'Compliant' : 'Non-Compliant'}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>{model.use_case}</span>
                    <span>Owner: {model.owner}</span>
                    <span>v{model.version}</span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
