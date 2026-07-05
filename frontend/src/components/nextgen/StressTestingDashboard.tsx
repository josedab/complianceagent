'use client'

import { Zap, BarChart3, AlertTriangle, TrendingUp } from 'lucide-react'
import { useStressScenarios } from '@/hooks/useNextgenApi'
import type { StressScenario } from '@/types/nextgen'

export default function StressTestingDashboard() {
  const { data: liveScenarios, loading, error, refetch } = useStressScenarios()

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
        <p className="text-red-800">Error loading Stress Testing: {error.message}</p>
        <button onClick={refetch} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const scenarios = liveScenarios ?? []
  const highSeverityCount = scenarios.filter(s => s.severity === 'high' || s.severity === 'critical').length
  const avgProbability = scenarios.length > 0
    ? (scenarios.reduce((sum, s) => sum + s.probability, 0) / scenarios.length * 100).toFixed(0)
    : '0'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Compliance Stress Testing</h1>
        <p className="text-gray-500">Monte Carlo simulations for compliance risk scenarios</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Scenarios</p>
            <Zap className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{scenarios.length}</p>
          <p className="mt-1 text-sm text-gray-500">Defined stress tests</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">High Severity</p>
            <BarChart3 className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">{highSeverityCount}</p>
          <p className="mt-1 text-sm text-gray-500">High/critical scenarios</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Avg Probability</p>
            <AlertTriangle className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{avgProbability}%</p>
          <p className="mt-1 text-sm text-gray-500">Average scenario likelihood</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Scenario Types</p>
            <TrendingUp className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">
            {new Set(scenarios.map(s => s.scenario_type)).size}
          </p>
          <p className="mt-1 text-sm text-gray-500">Distinct test types</p>
        </div>
      </div>

      {/* Scenario Cards */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="h-5 w-5 text-purple-500" />
          <h2 className="text-lg font-semibold text-gray-900">Stress Scenarios</h2>
        </div>
        {scenarios.length === 0 ? (
          <p className="text-gray-500 text-sm">No stress scenarios defined yet.</p>
        ) : (
          <div className="space-y-3">
            {scenarios.map((scenario: StressScenario) => (
              <div key={scenario.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{scenario.name}</span>
                    <span className="px-2 py-0.5 bg-white text-gray-600 text-xs rounded-full">{scenario.scenario_type.replace(/_/g, ' ')}</span>
                  </div>
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${scenario.severity === 'high' || scenario.severity === 'critical' ? 'text-red-700 bg-red-100' : scenario.severity === 'medium' ? 'text-yellow-700 bg-yellow-100' : 'text-green-700 bg-green-100'}`}>
                    {scenario.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mb-2">{scenario.description}</p>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>Probability: {(scenario.probability * 100).toFixed(0)}%</span>
                </div>
                <div className="mt-3">
                  <button className="px-3 py-1 bg-white border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50">
                    Run Simulation
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
