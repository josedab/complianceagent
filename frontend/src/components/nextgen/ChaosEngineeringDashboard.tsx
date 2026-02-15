'use client'

import { useState } from 'react'
import { Flame, Eye, EyeOff, Clock, AlertTriangle, CheckCircle, Play } from 'lucide-react'

type ExperimentStatus = 'scheduled' | 'running' | 'detected' | 'undetected' | 'rolled_back' | 'completed'

interface Experiment {
  id: string
  name: string
  description: string
  experimentType: string
  status: ExperimentStatus
  targetService: string
  targetEnvironment: string
  affectedFrameworks: string[]
  timeToDetect: number | null
  timeToRemediate: number | null
  detectionMethod: string
}

interface GameDay {
  id: string
  name: string
  description: string
  totalExperiments: number
  experimentsDetected: number
  teamReadinessScore: number
  avgDetectionTime: number
}

const statusConfig: Record<ExperimentStatus, { label: string; color: string; icon: typeof CheckCircle }> = {
  scheduled: { label: 'Scheduled', color: 'bg-gray-100 text-gray-700', icon: Clock },
  running: { label: 'Running', color: 'bg-blue-100 text-blue-700', icon: Play },
  detected: { label: 'Detected', color: 'bg-green-100 text-green-700', icon: Eye },
  undetected: { label: 'Undetected', color: 'bg-red-100 text-red-700', icon: EyeOff },
  rolled_back: { label: 'Rolled Back', color: 'bg-yellow-100 text-yellow-700', icon: AlertTriangle },
  completed: { label: 'Completed', color: 'bg-purple-100 text-purple-700', icon: CheckCircle },
}

const MOCK_EXPERIMENTS: Experiment[] = [
  { id: '1', name: 'Encryption Kill Switch', description: 'Disable TLS encryption on user API service.',
    experimentType: 'remove_encryption', status: 'completed', targetService: 'user-api', targetEnvironment: 'staging',
    affectedFrameworks: ['GDPR', 'PCI-DSS', 'HIPAA'], timeToDetect: 45, timeToRemediate: 180, detectionMethod: 'drift_detection' },
  { id: '2', name: 'Audit Log Black Hole', description: 'Silently drop audit log events for payment service.',
    experimentType: 'disable_audit_logs', status: 'completed', targetService: 'payment-service', targetEnvironment: 'staging',
    affectedFrameworks: ['PCI-DSS', 'SOC 2'], timeToDetect: null, timeToRemediate: null, detectionMethod: 'none' },
  { id: '3', name: 'PII Exposure Probe', description: 'Add unmasked PII fields to API responses.',
    experimentType: 'expose_pii', status: 'detected', targetService: 'profile-api', targetEnvironment: 'staging',
    affectedFrameworks: ['GDPR', 'HIPAA'], timeToDetect: 12.5, timeToRemediate: 60, detectionMethod: 'ide_linting' },
  { id: '4', name: 'Auth Bypass Injection', description: 'Disable JWT validation on admin endpoints.',
    experimentType: 'break_auth', status: 'scheduled', targetService: 'admin-api', targetEnvironment: 'staging',
    affectedFrameworks: ['SOC 2', 'ISO 27001'], timeToDetect: null, timeToRemediate: null, detectionMethod: '' },
]

const MOCK_GAME_DAY: GameDay = {
  id: '1', name: 'Q1 2025 Compliance Drill', description: 'Quarterly drill: 5 experiments across 3 services.',
  totalExperiments: 3, experimentsDetected: 2, teamReadinessScore: 72.5, avgDetectionTime: 28.75,
}

const MOCK_STATS = {
  totalExperiments: 4, detected: 2, undetected: 1,
  avgMttd: 28.75, avgMttr: 120, detectionRate: 0.67,
  gameDays: 1, controlsValidated: 4, blindSpots: 1,
}

export default function ChaosEngineeringDashboard() {
  const [activeTab, setActiveTab] = useState<'experiments' | 'gamedays' | 'stats'>('experiments')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><Flame className="h-7 w-7 text-orange-600" /> Compliance Chaos Engineering</h1>
        <p className="text-gray-500 mt-1">Inject compliance failures to validate detection and response capabilities</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Detection Rate</div>
          <div className={`text-2xl font-bold ${MOCK_STATS.detectionRate >= 0.8 ? 'text-green-600' : 'text-orange-600'}`}>{(MOCK_STATS.detectionRate * 100).toFixed(0)}%</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Avg MTTD</div>
          <div className="text-2xl font-bold">{MOCK_STATS.avgMttd.toFixed(0)}s</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Avg MTTR</div>
          <div className="text-2xl font-bold">{MOCK_STATS.avgMttr}s</div>
        </div>
        <div className="bg-red-50 rounded-lg border border-red-200 p-4">
          <div className="text-sm text-red-600">Blind Spots</div>
          <div className="text-2xl font-bold text-red-700">{MOCK_STATS.blindSpots}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        {(['experiments', 'gamedays', 'stats'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium ${activeTab === tab ? 'bg-white shadow text-orange-600' : 'text-gray-600'}`}>
            {tab === 'experiments' ? '🧪 Experiments' : tab === 'gamedays' ? '🎮 Game Days' : '📊 Stats'}
          </button>
        ))}
      </div>

      {activeTab === 'experiments' && (
        <div className="space-y-4">
          {MOCK_EXPERIMENTS.map(exp => {
            const cfg = statusConfig[exp.status]
            const StatusIcon = cfg.icon
            return (
              <div key={exp.id} className="bg-white rounded-lg border p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <StatusIcon className="h-4 w-4" />
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
                      <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{exp.targetService}</span>
                      <span className="text-xs text-gray-400">{exp.targetEnvironment}</span>
                    </div>
                    <h3 className="text-lg font-semibold">{exp.name}</h3>
                    <p className="text-gray-600 text-sm mt-1">{exp.description}</p>
                    <div className="flex gap-2 mt-2">
                      {exp.affectedFrameworks.map(fw => (
                        <span key={fw} className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded">{fw}</span>
                      ))}
                    </div>
                  </div>
                  <div className="text-right">
                    {exp.timeToDetect !== null ? (
                      <>
                        <div className="text-sm text-gray-500">MTTD</div>
                        <div className="text-lg font-bold">{exp.timeToDetect}s</div>
                        {exp.timeToRemediate !== null && (
                          <>
                            <div className="text-sm text-gray-500 mt-1">MTTR</div>
                            <div className="text-lg font-bold">{exp.timeToRemediate}s</div>
                          </>
                        )}
                      </>
                    ) : exp.status === 'completed' ? (
                      <div className="text-sm text-red-600 font-medium">⚠️ Not detected</div>
                    ) : null}
                  </div>
                </div>
                {exp.status === 'scheduled' && (
                  <button className="mt-3 px-4 py-2 bg-orange-600 text-white rounded-lg text-sm hover:bg-orange-700">
                    Run Experiment
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}

      {activeTab === 'gamedays' && (
        <div className="bg-white rounded-lg border p-5">
          <h3 className="text-lg font-semibold">{MOCK_GAME_DAY.name}</h3>
          <p className="text-gray-600 text-sm mt-1">{MOCK_GAME_DAY.description}</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div><div className="text-sm text-gray-500">Experiments</div><div className="text-xl font-bold">{MOCK_GAME_DAY.totalExperiments}</div></div>
            <div><div className="text-sm text-gray-500">Detected</div><div className="text-xl font-bold text-green-600">{MOCK_GAME_DAY.experimentsDetected}</div></div>
            <div><div className="text-sm text-gray-500">Readiness Score</div><div className="text-xl font-bold">{MOCK_GAME_DAY.teamReadinessScore}%</div></div>
            <div><div className="text-sm text-gray-500">Avg Detection</div><div className="text-xl font-bold">{MOCK_GAME_DAY.avgDetectionTime.toFixed(0)}s</div></div>
          </div>
        </div>
      )}

      {activeTab === 'stats' && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries({ 'Total Experiments': MOCK_STATS.totalExperiments, 'Detected': MOCK_STATS.detected, 'Undetected': MOCK_STATS.undetected,
            'Game Days': MOCK_STATS.gameDays, 'Controls Validated': MOCK_STATS.controlsValidated, 'Blind Spots Found': MOCK_STATS.blindSpots,
          }).map(([k, v]) => (
            <div key={k} className="bg-white rounded-lg border p-4">
              <div className="text-sm text-gray-500">{k}</div>
              <div className="text-2xl font-bold">{v}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
