'use client'

import { useState, useEffect } from 'react'
import { Target, BarChart3, TrendingUp, Award } from 'lucide-react'
import { api } from '@/lib/api'

const FALLBACK_ITEMS = [
  { id: 1, name: 'Data Protection', detail: 'Privacy controls score', value: '92%' },
  { id: 2, name: 'Access Management', detail: 'IAM posture assessment', value: '85%' },
  { id: 3, name: 'Incident Response', detail: 'IR readiness score', value: '84%' },
]

const FALLBACK_STATS = { score: '87%', controls: '234', trend: '+5%', percentile: '92nd' }

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

export default function PostureScoringDashboard() {
  const [items, setItems] = useState(FALLBACK_ITEMS)
  const [stats, setStats] = useState(FALLBACK_STATS)
  const [loading, setLoading] = useState(true)
  const [isDemo, setIsDemo] = useState(false)

  useEffect(() => {
    api.get('/posture-scoring/score')
      .then(res => {
        const data = res.data
        if (data) {
          setStats({
            score: data.score != null ? `${data.score}%` : FALLBACK_STATS.score,
            controls: String(data.controls ?? data.control_count ?? FALLBACK_STATS.controls),
            trend: data.trend != null ? `${data.trend > 0 ? '+' : ''}${data.trend}%` : FALLBACK_STATS.trend,
            percentile: data.percentile ? `${data.percentile}${ordinalSuffix(data.percentile)}` : FALLBACK_STATS.percentile,
          })
          const categories = data.categories || data.breakdown || data.items
          if (Array.isArray(categories) && categories.length > 0) {
            setItems(categories.map((c: Record<string, unknown>, i: number) => ({
              id: Number(c.id ?? i + 1),
              name: String(c.name || c.category || `Category ${i + 1}`),
              detail: String(c.detail || c.description || 'Posture assessment'),
              value: String(c.value || (c.score != null ? `${c.score}%` : '—')),
            })))
          }
          setIsDemo(false)
        } else {
          setIsDemo(true)
        }
      })
      .catch(() => { setIsDemo(true) })
      .finally(() => setLoading(false))
  }, [])

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
        <h1 className="text-2xl font-bold text-gray-900">Posture Scoring</h1>
        <p className="text-gray-500">Continuous compliance posture scoring and benchmarking</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Target className="h-5 w-5 text-blue-600" />} title="Score" value={stats.score} subtitle="Current posture" />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-green-600" />} title="Controls" value={stats.controls} subtitle="Evaluated" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-purple-600" />} title="Trend" value={stats.trend} subtitle="Month over month" />
        <StatCard icon={<Award className="h-5 w-5 text-orange-600" />} title="Percentile" value={stats.percentile} subtitle="Industry rank" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Category Breakdown</h2>
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail}</p>
              </div>
              <span className="text-sm text-gray-600">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function ordinalSuffix(n: number): string {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return s[(v - 20) % 10] || s[v] || s[0]
}
