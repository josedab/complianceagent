'use client'

import { Brain, TrendingUp, Globe, AlertTriangle } from 'lucide-react'
import { useMlPredictions, usePredictionAccuracy } from '@/hooks/useNextgenApi'

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

export default function PredictionsDashboard() {
  const { data: mlPredictions, loading: predsLoading, error: predsError, refetch: refetchPreds } = useMlPredictions()
  const { data: predictionAccuracy, loading: accuracyLoading, error: accuracyError, refetch: refetchAccuracy } = usePredictionAccuracy()

  const loading = predsLoading || accuracyLoading
  const error = predsError || accuracyError

  const refetch = () => { refetchPreds(); refetchAccuracy() }

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
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading Regulatory Predictions: {error.message}</p>
        <button onClick={refetch} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const predictions = mlPredictions ?? []
  const highConfidence = predictions.filter(p => {
    const conf = p['confidence'] ?? p['risk_level'] ?? p['value']
    return String(conf).toLowerCase() === 'high' || Number(conf) >= 0.8
  }).length
  const accuracyScore = predictionAccuracy
    ? String(predictionAccuracy['accuracy'] ?? predictionAccuracy['score'] ?? '—')
    : '—'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Predictions</h1>
        <p className="text-gray-500">AI-powered regulatory change predictions</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Brain className="h-5 w-5 text-blue-600" />} title="Predictions" value={String(predictions.length)} subtitle="Active" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-green-600" />} title="High Confidence" value={String(highConfidence)} subtitle="Risk signals" />
        <StatCard icon={<Globe className="h-5 w-5 text-purple-600" />} title="Model Accuracy" value={accuracyScore} subtitle="Prediction accuracy" />
        <StatCard icon={<AlertTriangle className="h-5 w-5 text-orange-600" />} title="Upcoming" value={String(predictions.length)} subtitle="Changes expected" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Predictions ({predictions.length})</h2>
        {predictions.length === 0 ? (
          <p className="text-gray-500 text-sm">No predictions available yet.</p>
        ) : (
          <div className="space-y-3">
            {predictions.map((item, i) => {
              const id = item['id'] ?? i
              const name = String(item['name'] ?? item['title'] ?? 'Unknown')
              const detail = String(item['detail'] ?? item['description'] ?? '')
              const value = String(item['value'] ?? item['confidence'] ?? item['risk_level'] ?? '—')
              const valueUpper = value.toLowerCase()
              return (
                <div key={String(id)} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
                  <div>
                    <span className="font-medium text-gray-900">{name}</span>
                    {detail && <p className="text-xs text-gray-500">{detail}</p>}
                  </div>
                  <span className={`text-sm font-medium ${valueUpper === 'high' ? 'text-red-600' : valueUpper === 'medium' ? 'text-yellow-600' : 'text-green-600'}`}>{value}</span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
