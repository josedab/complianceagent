'use client'

import { Zap, BarChart3, AlertTriangle, TrendingUp } from 'lucide-react'
import { useStressScenarios } from '@/hooks/useNextgenApi'
import type { StressScenario } from '@/types/nextgen'

interface StressScenarioDisplay extends StressScenario {
  type: string;
  simulations: number;
  exposure: number;
  risk_score: number;
  status: string;
  last_run: string;
}

const MOCK_SCENARIOS: StressScenarioDisplay[] = [
  { id: 'ss1', name: 'GDPR Fine Escalation', scenario_type: 'monte_carlo', description: 'GDPR fine escalation scenario', parameters: {}, probability: 0.35, severity: 'high', type: 'monte_carlo', simulations: 5000, exposure: 1200000, risk_score: 8.1, status: 'completed', last_run: '2026-03-10T10:00:00Z' },
  { id: 'ss2', name: 'Cross-Border Transfer Ban', scenario_type: 'scenario_analysis', description: 'Cross-border transfer ban scenario', parameters: {}, probability: 0.12, severity: 'medium', type: 'scenario_analysis', simulations: 3000, exposure: 450000, risk_score: 6.4, status: 'completed', last_run: '2026-03-09T14:00:00Z' },
  { id: 'ss3', name: 'Data Breach Response', scenario_type: 'monte_carlo', description: 'Data breach response scenario', parameters: {}, probability: 0.22, severity: 'high', type: 'monte_carlo', simulations: 8000, exposure: 340000, risk_score: 7.8, status: 'completed', last_run: '2026-03-11T08:00:00Z' },
  { id: 'ss4', name: 'AI Act Enforcement', scenario_type: 'stress_test', description: 'AI Act enforcement scenario', parameters: {}, probability: 0.45, severity: 'medium', type: 'stress_test', simulations: 4000, exposure: 280000, risk_score: 5.9, status: 'ready', last_run: '2026-03-08T16:00:00Z' },
  { id: 'ss5', name: 'Supply Chain Compliance', scenario_type: 'monte_carlo', description: 'Supply chain compliance scenario', parameters: {}, probability: 0.18, severity: 'low', type: 'monte_carlo', simulations: 2000, exposure: 95000, risk_score: 4.2, status: 'completed', last_run: '2026-03-07T12:00:00Z' },
  { id: 'ss6', name: 'Encryption Standard Shift', scenario_type: 'scenario_analysis', description: 'Encryption standard shift scenario', parameters: {}, probability: 0.08, severity: 'low', type: 'scenario_analysis', simulations: 2000, exposure: 35000, risk_score: 3.1, status: 'ready', last_run: '2026-03-06T09:00:00Z' },
]

export default function StressTestingDashboard() {
  const { data: liveScenarios } = useStressScenarios()

  const scenarios = (liveScenarios as StressScenarioDisplay[] | null) || MOCK_SCENARIOS
  const totalSimulations = scenarios.reduce((sum, s) => sum + s.simulations, 0)
  const totalExposure = scenarios.reduce((sum, s) => sum + s.exposure, 0)
  const avgRisk = (scenarios.reduce((sum, s) => sum + s.risk_score, 0) / scenarios.length).toFixed(1)

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
            <p className="text-sm font-medium text-gray-500">Simulations Run</p>
            <BarChart3 className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">{(totalSimulations / 1000).toFixed(0)}K</p>
          <p className="mt-1 text-sm text-gray-500">Total iterations</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Aggregate Exposure</p>
            <AlertTriangle className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">${(totalExposure / 1000000).toFixed(1)}M</p>
          <p className="mt-1 text-sm text-gray-500">Potential risk value</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Risk Score</p>
            <TrendingUp className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{avgRisk}</p>
          <p className="mt-1 text-sm text-gray-500">Weighted average</p>
        </div>
      </div>

      {/* Scenario Cards */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="h-5 w-5 text-purple-500" />
          <h2 className="text-lg font-semibold text-gray-900">Stress Scenarios</h2>
        </div>
        <div className="space-y-3">
          {scenarios.map(scenario => (
            <div key={scenario.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{scenario.name}</span>
                  <span className="px-2 py-0.5 bg-white text-gray-600 text-xs rounded-full">{scenario.type.replace('_', ' ')}</span>
                </div>
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${scenario.status === 'completed' ? 'text-green-700 bg-green-100' : 'text-blue-700 bg-blue-100'}`}>
                  {scenario.status}
                </span>
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>Probability: {(scenario.probability * 100).toFixed(0)}%</span>
                <span>Exposure: ${(scenario.exposure / 1000).toFixed(0)}K</span>
                <span>Risk: {scenario.risk_score}/10</span>
                <span>{scenario.simulations.toLocaleString()} runs</span>
              </div>
              <div className="mt-3">
                <button className="px-3 py-1 bg-white border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50">
                  Run Simulation
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
