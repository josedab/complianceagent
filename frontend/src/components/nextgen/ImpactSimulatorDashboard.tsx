'use client'

import { Zap, BarChart3, Play } from 'lucide-react'
import { useImpactScenarios } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ImpactSimulatorDashboard() {
  const { data: scenarios, loading, error, refetch } = useImpactScenarios()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Impact Simulator</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{[...Array(3)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Impact Simulator</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Impact Simulator: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Impact Simulator</h1>
        <p className="text-gray-500">Simulate the blast radius of compliance policy changes before applying them</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard icon={<Play className="w-5 h-5 text-blue-500" />} title="Scenarios" value={String(scenarios?.length ?? 0)} subtitle="Available scenarios" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-purple-500" />} title="Regulations" value={String(scenarios ? new Set(scenarios.map(s => s.regulation)).size : 0)} subtitle="Covered regulations" />
        <StatCard icon={<Zap className="w-5 h-5 text-yellow-500" />} title="Categories" value={String(scenarios ? new Set(scenarios.map(s => s.category)).size : 0)} subtitle="Scenario categories" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Prebuilt Scenarios</h2>
        {!scenarios || scenarios.length === 0 ? (
          <p className="text-gray-500">No impact scenarios available.</p>
        ) : (
          <div className="space-y-3">
            {scenarios.map((scenario) => (
              <div key={scenario.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Zap className="w-5 h-5 text-yellow-500" />
                  <div>
                    <p className="font-medium text-gray-900">{scenario.name}</p>
                    <p className="text-sm text-gray-500">{scenario.regulation} · {scenario.category} · {scenario.description}</p>
                  </div>
                </div>
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                  {scenario.difficulty}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
