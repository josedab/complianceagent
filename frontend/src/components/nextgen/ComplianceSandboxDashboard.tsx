'use client'

import { useState } from 'react'
import { FlaskConical, Shield, Clock, Play } from 'lucide-react'
import { useSandboxScenarios, useCreateSandboxEnvironment } from '@/hooks/useNextgenApi'
import type { SandboxEnvironment } from '@/types/nextgen'

const difficultyColors: Record<string, string> = {
  beginner: 'bg-green-100 text-green-700',
  intermediate: 'bg-yellow-100 text-yellow-700',
  advanced: 'bg-red-100 text-red-700',
}

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
  const { data: scenarios, loading, error, refetch } = useSandboxScenarios()
  const { mutate: startEnvironment, loading: starting } = useCreateSandboxEnvironment()
  const [environments, setEnvironments] = useState<Record<string, SandboxEnvironment>>({})
  const [startError, setStartError] = useState<string | null>(null)

  async function handleStart(scenarioId: string) {
    setStartError(null)
    try {
      const env = await startEnvironment(scenarioId)
      setEnvironments(prev => ({ ...prev, [scenarioId]: env }))
    } catch {
      setStartError('Failed to start sandbox environment')
    }
  }

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
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Compliance Sandbox</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading sandbox scenarios: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const items = scenarios || []
  const activeCount = Object.values(environments).filter(e => e.status === 'active' || e.status === 'provisioning').length
  const regulations = new Set(items.map(s => s.regulation)).size
  const totalMinutes = items.reduce((sum, s) => sum + s.estimated_minutes, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Sandbox</h1>
        <p className="text-gray-500">Isolated environments for compliance testing</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FlaskConical className="h-5 w-5 text-blue-600" />} title="Scenarios" value={String(items.length)} subtitle="Total environments" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Active" value={String(activeCount)} subtitle="Running now" />
        <StatCard icon={<Clock className="h-5 w-5 text-purple-600" />} title="Est. Time" value={`${totalMinutes}m`} subtitle="Across all scenarios" />
        <StatCard icon={<Play className="h-5 w-5 text-orange-600" />} title="Regulations" value={String(regulations)} subtitle="Covered" />
      </div>
      {startError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">{startError}</div>
      )}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Scenarios ({items.length})</h2>
        {items.length === 0 ? (
          <p className="text-gray-500 text-sm">No sandbox scenarios available.</p>
        ) : (
          <div className="space-y-3">
            {items.map((item) => {
              const env = environments[item.id]
              return (
                <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{item.title}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${difficultyColors[item.difficulty] || 'bg-gray-100 text-gray-700'}`}>{item.difficulty}</span>
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">{item.regulation}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{item.description} · ~{item.estimated_minutes}m</p>
                  </div>
                  {env ? (
                    <span className="text-sm font-medium text-green-600">{env.status} ({env.progress}%)</span>
                  ) : (
                    <button
                      onClick={() => handleStart(item.id)}
                      disabled={starting}
                      className="px-3 py-1 bg-primary-600 text-white rounded text-sm hover:bg-primary-700 disabled:opacity-50"
                    >
                      Start
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
