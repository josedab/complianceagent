'use client'

import { useState, useEffect } from 'react'
import { Server, Shield, FileCode, CheckCircle } from 'lucide-react'
import { api } from '@/lib/api'

const FALLBACK_ITEMS = [
  { id: 1, name: 'Terraform Policies', detail: 'AWS resource compliance', value: '32 rules' },
  { id: 2, name: 'Kubernetes Policies', detail: 'Container security standards', value: '28 rules' },
  { id: 3, name: 'CloudFormation', detail: 'Infrastructure guardrails', value: '19 rules' },
]

const FALLBACK_STATS = { policies: '89', scans: '2.3K', violations: '156', autoFixed: '134' }

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

export default function IaCPolicyDashboard() {
  const [items, setItems] = useState(FALLBACK_ITEMS)
  const [stats, setStats] = useState(FALLBACK_STATS)
  const [loading, setLoading] = useState(true)
  const [isDemo, setIsDemo] = useState(false)

  useEffect(() => {
    api.get('/iac-scanner/scans')
      .then(res => {
        const data = res.data
        const scans = data?.items || data?.scans || (Array.isArray(data) ? data : null)
        if (scans && scans.length > 0) {
          setItems(scans.slice(0, 10).map((s: Record<string, unknown>, i: number) => ({
            id: s.id ?? i + 1,
            name: s.name || s.platform || s.title || `Scan #${i + 1}`,
            detail: s.detail || s.description || s.status || 'IaC scan result',
            value: s.value || s.violations || s.result || '—',
          })))
          setStats({
            policies: String(data.policy_count ?? data.policies ?? FALLBACK_STATS.policies),
            scans: String(scans.length),
            violations: String((data.violation_count ?? data.violations ?? scans.reduce((sum: number, s: Record<string, unknown>) => sum + (Number(s.violations) || 0), 0)) || FALLBACK_STATS.violations),
            autoFixed: String(data.auto_fixed ?? data.remediated ?? FALLBACK_STATS.autoFixed),
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
        <h1 className="text-2xl font-bold text-gray-900">IaC Policy Engine</h1>
        <p className="text-gray-500">Policy enforcement for Infrastructure as Code</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Server className="h-5 w-5 text-blue-600" />} title="Policies" value={stats.policies} subtitle="Active" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Scans" value={stats.scans} subtitle="This month" />
        <StatCard icon={<FileCode className="h-5 w-5 text-purple-600" />} title="Violations" value={stats.violations} subtitle="Found" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-orange-600" />} title="Auto-Fixed" value={stats.autoFixed} subtitle="Remediated" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">IaC Scan Results</h2>
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
