'use client'

import { useState, useEffect } from 'react'
import { FlaskConical, Shield, Code, Play } from 'lucide-react'
import { api } from '@/lib/api'

interface SandboxScenario {
  id: string | number
  name: string
  detail: string
  status: string
}

const FALLBACK_SCENARIOS: SandboxScenario[] = [
  { id: 1, name: 'Policy Sandbox', detail: 'Testing regulatory policies', status: 'Active' },
  { id: 2, name: 'Rule Engine Sandbox', detail: 'Validating compliance rules', status: 'Active' },
  { id: 3, name: 'Audit Sandbox', detail: 'Simulating audit scenarios', status: 'Idle' },
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

export default function ComplianceSandboxDashboard() {
  const [scenarios, setScenarios] = useState<SandboxScenario[]>(FALLBACK_SCENARIOS)
  const [loading, setLoading] = useState(true)
  const [isDemo, setIsDemo] = useState(false)

  useEffect(() => {
    api.get('/sandbox/scenarios')
      .then(res => {
        const data = res.data
        const items = data?.items || data?.scenarios || (Array.isArray(data) ? data : null)
        if (items && items.length > 0) {
          setScenarios(items.map((s: Record<string, unknown>, i: number) => ({
            id: s.id || `sb-${i}`,
            name: (s.name || s.title || 'Unknown') as string,
            detail: (s.detail || s.description || '') as string,
            status: (s.status || 'Idle') as string,
          })))
          setIsDemo(false)
        } else {
          setIsDemo(true)
        }
      })
      .catch(() => { setIsDemo(true) })
      .finally(() => setLoading(false))
  }, [])

  const activeCount = scenarios.filter(s => s.status === 'Active' || s.status === 'active').length

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
        <h1 className="text-2xl font-bold text-gray-900">Compliance Sandbox</h1>
        <p className="text-gray-500">Isolated environments for compliance testing</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FlaskConical className="h-5 w-5 text-blue-600" />} title="Scenarios" value={String(scenarios.length)} subtitle="Total environments" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Active" value={String(activeCount)} subtitle="Running now" />
        <StatCard icon={<Code className="h-5 w-5 text-purple-600" />} title="Rules" value="48" subtitle="Configured" />
        <StatCard icon={<Play className="h-5 w-5 text-orange-600" />} title="Executions" value="156" subtitle="This week" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Scenarios ({scenarios.length})</h2>
        <div className="space-y-3">
          {scenarios.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail}</p>
              </div>
              <span className={`text-sm font-medium ${item.status === 'Active' || item.status === 'active' ? 'text-green-600' : 'text-gray-500'}`}>{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
