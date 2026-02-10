'use client'

import { useState } from 'react'
import { FlaskConical, Play, Award, Clock } from 'lucide-react'
import { useSandboxScenarios, useCreateSandboxEnvironment } from '@/hooks/useNextgenApi'
import type { SandboxScenario, SandboxEnvironment } from '@/types/nextgen'

const MOCK_SCENARIOS: SandboxScenario[] = [
  { id: 'gdpr-101', title: 'GDPR Data Protection Fundamentals', description: 'Fix PII exposure, missing consent tracking, and excessive retention in a SaaS microservice', regulation: 'GDPR', difficulty: 'beginner', estimated_minutes: 30, tags: ['gdpr', 'data-privacy', 'beginner'] },
  { id: 'hipaa-201', title: 'HIPAA PHI Security', description: 'Secure PHI storage, encryption, and access controls in a healthcare application', regulation: 'HIPAA', difficulty: 'intermediate', estimated_minutes: 45, tags: ['hipaa', 'phi', 'encryption'] },
  { id: 'pci-301', title: 'PCI-DSS Payment Security', description: 'Implement card data tokenization and remove plaintext card numbers from logs', regulation: 'PCI-DSS', difficulty: 'advanced', estimated_minutes: 60, tags: ['pci-dss', 'tokenization', 'payment'] },
  { id: 'ai-act-101', title: 'EU AI Act Compliance', description: 'Add risk classification, transparency disclosures, and human oversight to an AI system', regulation: 'EU AI Act', difficulty: 'intermediate', estimated_minutes: 45, tags: ['eu-ai-act', 'transparency', 'risk'] },
]

const MOCK_ENVS: SandboxEnvironment[] = [
  { id: 'env1', scenario_id: 'gdpr-101', status: 'completed', progress: 100, started_at: '2026-02-10T10:00:00Z' },
  { id: 'env2', scenario_id: 'hipaa-201', status: 'active', progress: 65, started_at: '2026-02-13T14:00:00Z' },
]

const difficultyColors = { beginner: 'bg-green-100 text-green-700', intermediate: 'bg-yellow-100 text-yellow-700', advanced: 'bg-red-100 text-red-700' }

export default function ComplianceSandboxDashboard() {
  const { data: liveScenarios } = useSandboxScenarios()
  const { mutate: createEnvironment, loading: creating } = useCreateSandboxEnvironment()
  const [environments, setEnvironments] = useState<SandboxEnvironment[]>(MOCK_ENVS)

  const scenarios = liveScenarios || MOCK_SCENARIOS
  const completedCount = environments.filter(e => e.status === 'completed').length
  const activeCount = environments.filter(e => e.status === 'active').length

  const handleLaunch = async (scenarioId: string) => {
    try {
      const env = await createEnvironment(scenarioId)
      setEnvironments(prev => [...prev, env])
    } catch {
      // Keep current state on error
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Training Sandbox</h1>
        <p className="text-gray-500">Interactive compliance training with real-world scenarios</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FlaskConical className="h-5 w-5 text-blue-600" />} title="Scenarios" value={scenarios.length.toString()} subtitle="Available training modules" />
        <StatCard icon={<Play className="h-5 w-5 text-green-600" />} title="Active" value={activeCount.toString()} subtitle="In progress" />
        <StatCard icon={<Award className="h-5 w-5 text-purple-600" />} title="Completed" value={completedCount.toString()} subtitle="Scenarios finished" />
        <StatCard icon={<Clock className="h-5 w-5 text-orange-600" />} title="Avg. Time" value="40 min" subtitle="Per scenario" />
      </div>

      {/* Active Environments */}
      {environments.filter(e => e.status === 'active').length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Training</h2>
          {environments.filter(e => e.status === 'active').map(env => {
            const scenario = scenarios.find(s => s.id === env.scenario_id)
            return (
              <div key={env.id} className="p-4 rounded-lg border border-primary-200 bg-primary-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">{scenario?.title || env.scenario_id}</span>
                  <span className="text-sm text-primary-700">{env.progress}% complete</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div className="h-full bg-primary-500 rounded-full transition-all" style={{ width: `${env.progress}%` }} />
                </div>
                <button className="mt-3 px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700">
                  Continue Training
                </button>
              </div>
            )
          })}
        </div>
      )}

      {/* Scenarios */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Training Scenarios</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {scenarios.map(scenario => {
            const env = environments.find(e => e.scenario_id === scenario.id)
            const isCompleted = env?.status === 'completed'
            return (
              <div key={scenario.id} className={`p-4 rounded-lg border ${isCompleted ? 'border-green-200 bg-green-50' : 'border-gray-200'}`}>
                <div className="flex items-center gap-2 mb-2">
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${difficultyColors[scenario.difficulty]}`}>{scenario.difficulty}</span>
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">{scenario.regulation}</span>
                  {isCompleted && <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">✓ Done</span>}
                </div>
                <h3 className="font-medium text-gray-900">{scenario.title}</h3>
                <p className="text-sm text-gray-500 mt-1">{scenario.description}</p>
                <div className="flex items-center justify-between mt-3">
                  <span className="text-xs text-gray-400">⏱ {scenario.estimated_minutes} minutes</span>
                  <button
                    onClick={() => !isCompleted && handleLaunch(scenario.id)}
                    disabled={creating || isCompleted}
                    className={`px-3 py-1 rounded text-sm font-medium ${isCompleted ? 'bg-gray-100 text-gray-600' : 'bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50'}`}
                  >
                    {isCompleted ? 'Review' : creating ? 'Starting...' : 'Start'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between"><p className="text-sm font-medium text-gray-500">{title}</p>{icon}</div>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
    </div>
  )
}
