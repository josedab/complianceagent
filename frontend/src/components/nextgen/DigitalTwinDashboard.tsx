'use client'

import { useState } from 'react'
import { Layers, Activity, GitCompare, AlertTriangle, Play, Clock } from 'lucide-react'

interface TwinSnapshot {
  id: string
  repository: string
  overall_score: number
  issues_count: number
  timestamp: string
}

interface SimulationResult {
  id: string
  scenario: string
  before_score: number
  after_score: number
  delta: number
  status: string
}

const MOCK_SNAPSHOTS: TwinSnapshot[] = [
  { id: 'snap-1', repository: 'api-service', overall_score: 87.5, issues_count: 12, timestamp: '2026-02-20T10:00:00Z' },
  { id: 'snap-2', repository: 'auth-service', overall_score: 92.1, issues_count: 5, timestamp: '2026-02-20T09:30:00Z' },
  { id: 'snap-3', repository: 'payment-service', overall_score: 78.3, issues_count: 23, timestamp: '2026-02-20T09:00:00Z' },
]

const MOCK_SIMULATIONS: SimulationResult[] = [
  { id: 'sim-1', scenario: 'EU AI Act — High-risk classification', before_score: 87.5, after_score: 72.1, delta: -15.4, status: 'completed' },
  { id: 'sim-2', scenario: 'GDPR — New data portability requirements', before_score: 92.1, after_score: 88.5, delta: -3.6, status: 'completed' },
  { id: 'sim-3', scenario: 'PCI-DSS 4.0 — API security mandates', before_score: 78.3, after_score: 65.0, delta: -13.3, status: 'completed' },
]

export default function DigitalTwinDashboard() {
  const [activeTab, setActiveTab] = useState<'snapshots' | 'simulations'>('snapshots')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Compliance Digital Twin</h1>
        <p className="text-gray-500 mt-1">Real-time virtual replica of your compliance posture with what-if simulation</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><Layers className="w-4 h-4" /> Repositories</div>
          <div className="text-2xl font-bold">{MOCK_SNAPSHOTS.length}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><Activity className="w-4 h-4" /> Avg Score</div>
          <div className="text-2xl font-bold">{(MOCK_SNAPSHOTS.reduce((a, s) => a + s.overall_score, 0) / MOCK_SNAPSHOTS.length).toFixed(1)}%</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><AlertTriangle className="w-4 h-4" /> Total Issues</div>
          <div className="text-2xl font-bold">{MOCK_SNAPSHOTS.reduce((a, s) => a + s.issues_count, 0)}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><Play className="w-4 h-4" /> Simulations</div>
          <div className="text-2xl font-bold">{MOCK_SIMULATIONS.length}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b">
        <button onClick={() => setActiveTab('snapshots')} className={`pb-2 px-1 text-sm font-medium ${activeTab === 'snapshots' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}>
          <Layers className="w-4 h-4 inline mr-1" /> Live Snapshots
        </button>
        <button onClick={() => setActiveTab('simulations')} className={`pb-2 px-1 text-sm font-medium ${activeTab === 'simulations' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}>
          <GitCompare className="w-4 h-4 inline mr-1" /> What-If Simulations
        </button>
      </div>

      {/* Content */}
      {activeTab === 'snapshots' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border">
          <table className="w-full">
            <thead>
              <tr className="border-b text-left text-sm text-gray-500">
                <th className="p-3">Repository</th>
                <th className="p-3">Score</th>
                <th className="p-3">Issues</th>
                <th className="p-3">Last Updated</th>
              </tr>
            </thead>
            <tbody>
              {MOCK_SNAPSHOTS.map(snap => (
                <tr key={snap.id} className="border-b last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="p-3 font-medium">{snap.repository}</td>
                  <td className="p-3">
                    <span className={`font-bold ${snap.overall_score >= 85 ? 'text-green-600' : snap.overall_score >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {snap.overall_score}%
                    </span>
                  </td>
                  <td className="p-3">{snap.issues_count}</td>
                  <td className="p-3 text-sm text-gray-500"><Clock className="w-3 h-3 inline mr-1" />{new Date(snap.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'simulations' && (
        <div className="space-y-3">
          {MOCK_SIMULATIONS.map(sim => (
            <div key={sim.id} className="bg-white dark:bg-gray-800 rounded-lg border p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium">{sim.scenario}</h3>
                  <p className="text-sm text-gray-500 mt-1">Score impact: {sim.before_score}% → {sim.after_score}%</p>
                </div>
                <span className={`text-lg font-bold ${sim.delta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {sim.delta > 0 ? '+' : ''}{sim.delta.toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* v2: Live Posture Tracking */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🔴 Live Posture Tracking</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-blue-50 border border-blue-200">
            <p className="text-sm font-medium text-blue-700">Time-Travel Queries</p>
            <p className="text-2xl font-bold text-blue-900 mt-1">View posture at any point in time</p>
            <p className="text-xs text-blue-600 mt-2">Powered by event-driven snapshots</p>
          </div>
          <div className="p-4 rounded-lg bg-red-50 border border-red-200">
            <p className="text-sm font-medium text-red-700">Blast Radius Analysis</p>
            <p className="text-2xl font-bold text-red-900 mt-1">Impact of regulation changes</p>
            <p className="text-xs text-red-600 mt-2">Estimates remediation effort in hours</p>
          </div>
          <div className="p-4 rounded-lg bg-green-50 border border-green-200">
            <p className="text-sm font-medium text-green-700">Event-Driven Snapshots</p>
            <p className="text-2xl font-bold text-green-900 mt-1">Auto-capture on changes</p>
            <p className="text-xs text-green-600 mt-2">Regulation changes, deploys, scans</p>
          </div>
        </div>
      </div>
    </div>
  )
}
