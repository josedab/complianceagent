'use client'

import { useState, useEffect } from 'react'
import { FileCheck, Shield, Clock, CheckCircle } from 'lucide-react'
import { api } from '@/lib/api'

const FALLBACK_ITEMS = [
  { id: 1, name: 'SOC 2 Type II', detail: 'Evidence collection 90% complete', value: '90%' },
  { id: 2, name: 'ISO 27001', detail: 'Controls mapping verified', value: '85%' },
  { id: 3, name: 'GDPR Assessment', detail: 'Data flow documented', value: '78%' },
]

const FALLBACK_STATS = { audits: '8', evidence: '234', readiness: '96%', avgTime: '2.1d' }

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

export default function AuditAutopilotDashboard() {
  const [items, setItems] = useState(FALLBACK_ITEMS)
  const [stats, setStats] = useState(FALLBACK_STATS)
  const [loading, setLoading] = useState(true)
  const [isDemo, setIsDemo] = useState(false)

  useEffect(() => {
    api.get('/audit/?limit=10')
      .then(res => {
        const data = res.data?.items || res.data
        if (Array.isArray(data) && data.length > 0) {
          setItems(data.slice(0, 10).map((entry: Record<string, unknown>, i: number) => ({
            id: Number(entry.id ?? i + 1),
            name: String(entry.name || entry.title || entry.framework || `Audit #${i + 1}`),
            detail: String(entry.detail || entry.description || entry.status || 'Audit entry'),
            value: String(entry.value || entry.score || entry.result || '—'),
          })))
          setStats({
            audits: String(data.length),
            evidence: String(res.data?.evidence_count ?? FALLBACK_STATS.evidence),
            readiness: res.data?.readiness ? `${res.data.readiness}%` : FALLBACK_STATS.readiness,
            avgTime: res.data?.avg_time || FALLBACK_STATS.avgTime,
          })
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
        <h1 className="text-2xl font-bold text-gray-900">Audit Preparation Autopilot</h1>
        <p className="text-gray-500">Automated audit preparation and evidence collection</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FileCheck className="h-5 w-5 text-blue-600" />} title="Audits" value={stats.audits} subtitle="In progress" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Evidence" value={stats.evidence} subtitle="Items collected" />
        <StatCard icon={<Clock className="h-5 w-5 text-purple-600" />} title="Readiness" value={stats.readiness} subtitle="Overall score" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-orange-600" />} title="Avg Time" value={stats.avgTime} subtitle="Per audit" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Audit Entries</h2>
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
