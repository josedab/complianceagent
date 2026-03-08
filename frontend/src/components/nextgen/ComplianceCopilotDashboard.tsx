'use client'

import { useState, useEffect } from 'react'
import { Bot, AlertTriangle, CheckCircle, BookOpen } from 'lucide-react'
import { api } from '@/lib/api'

const FALLBACK_VIOLATIONS = [
  { id: 1, rule: 'GDPR Art. 17 – Right to Erasure', severity: 'Critical', status: 'Open', detectedAt: '2024-03-15' },
  { id: 2, rule: 'SOC2 CC6.1 – Logical Access', severity: 'High', status: 'In Review', detectedAt: '2024-03-14' },
  { id: 3, rule: 'HIPAA §164.312 – Access Control', severity: 'Medium', status: 'Remediated', detectedAt: '2024-03-12' },
  { id: 4, rule: 'PCI-DSS Req 8 – Authentication', severity: 'Low', status: 'Open', detectedAt: '2024-03-10' },
]

const FALLBACK_STATS = { score: '94%', frameworks: 38, gaps: 4, scans: 142 }

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

export default function ComplianceCopilotDashboard() {
  const [violations, setViolations] = useState(FALLBACK_VIOLATIONS)
  const [stats, setStats] = useState(FALLBACK_STATS)
  const [loading, setLoading] = useState(true)
  const [isDemo, setIsDemo] = useState(false)

  useEffect(() => {
    let demo = false
    Promise.all([
      api.get('/compliance/status').catch(() => { demo = true; return null }),
      api.get('/audit/actions?status=pending').catch(() => { demo = true; return null }),
    ]).then(([statusRes, actionsRes]) => {
      if (statusRes?.data) {
        const d = statusRes.data
        setStats({
          score: d.score != null ? `${d.score}%` : FALLBACK_STATS.score,
          frameworks: d.frameworks ?? d.framework_count ?? FALLBACK_STATS.frameworks,
          gaps: d.gaps ?? d.gap_count ?? FALLBACK_STATS.gaps,
          scans: d.scans ?? d.scan_count ?? FALLBACK_STATS.scans,
        })
      }
      if (actionsRes?.data) {
        const items = actionsRes.data?.items || actionsRes.data
        if (Array.isArray(items) && items.length > 0) setViolations(items)
      }
      setIsDemo(demo)
    }).finally(() => setLoading(false))
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
        <h1 className="text-2xl font-bold text-gray-900">AI Compliance Co-Pilot</h1>
        <p className="text-gray-500">Intelligent compliance monitoring and violation detection</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Bot className="w-5 h-5 text-blue-500" />} title="AI Scans Today" value={String(stats.scans)} subtitle="Automated checks run" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-red-500" />} title="Open Violations" value={String(stats.gaps)} subtitle="Require attention" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-500" />} title="Compliance Score" value={stats.score} subtitle="Across all frameworks" />
        <StatCard icon={<BookOpen className="w-5 h-5 text-purple-500" />} title="Policies Tracked" value={String(stats.frameworks)} subtitle="Active policy rules" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Violations</h2>
        <div className="space-y-3">
          {violations.map((v) => (
            <div key={v.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                <div>
                  <p className="font-medium text-gray-900">{v.rule}</p>
                  <p className="text-sm text-gray-500">Detected {v.detectedAt} · {v.status}</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                v.severity === 'Critical' ? 'bg-red-100 text-red-700' :
                v.severity === 'High' ? 'bg-orange-100 text-orange-700' :
                v.severity === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {v.severity}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
