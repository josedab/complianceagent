'use client'

import { useState, useEffect } from 'react'
import { Brain, TrendingUp, Globe, AlertTriangle } from 'lucide-react'
import { api } from '@/lib/api'

interface Prediction {
  id: string | number
  name: string
  detail: string
  value: string
}

const FALLBACK_PREDICTIONS: Prediction[] = [
  { id: 1, name: 'EU AI Act Enforcement', detail: 'Expected implementation Q3', value: 'High' },
  { id: 2, name: 'US Privacy Law', detail: 'Federal bill probability', value: 'Medium' },
  { id: 3, name: 'APAC Data Rules', detail: 'Cross-border changes', value: 'High' },
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

export default function PredictionsDashboard() {
  const [predictions, setPredictions] = useState<Prediction[]>(FALLBACK_PREDICTIONS)
  const [loading, setLoading] = useState(true)
  const [isDemo, setIsDemo] = useState(false)

  useEffect(() => {
    api.get('/predictions/predictions')
      .then(res => {
        const data = res.data
        const items = data?.items || data?.predictions || (Array.isArray(data) ? data : null)
        if (items && items.length > 0) {
          setPredictions(items.map((p: Record<string, unknown>, i: number) => ({
            id: p.id || `pred-${i}`,
            name: (p.name || p.title || 'Unknown') as string,
            detail: (p.detail || p.description || '') as string,
            value: (p.value || p.confidence || p.risk_level || 'Medium') as string,
          })))
          setIsDemo(false)
        } else {
          setIsDemo(true)
        }
      })
      .catch(() => { setIsDemo(true) })
      .finally(() => setLoading(false))
  }, [])

  const highConfidence = predictions.filter(p => p.value === 'High').length

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

  return (
    <div className="space-y-6">
      {isDemo && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-2 rounded-lg text-sm">
          Using demo data — connect backend for live data
        </div>
      )}

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Predictions</h1>
        <p className="text-gray-500">AI-powered regulatory change predictions</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Brain className="h-5 w-5 text-blue-600" />} title="Predictions" value={String(predictions.length)} subtitle="Active" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-green-600" />} title="High Confidence" value={String(highConfidence)} subtitle="Risk signals" />
        <StatCard icon={<Globe className="h-5 w-5 text-purple-600" />} title="Regions" value="12" subtitle="Monitored" />
        <StatCard icon={<AlertTriangle className="h-5 w-5 text-orange-600" />} title="Upcoming" value={String(predictions.length)} subtitle="Changes expected" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Predictions ({predictions.length})</h2>
        <div className="space-y-3">
          {predictions.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail}</p>
              </div>
              <span className={`text-sm font-medium ${item.value === 'High' ? 'text-red-600' : item.value === 'Medium' ? 'text-yellow-600' : 'text-green-600'}`}>{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
