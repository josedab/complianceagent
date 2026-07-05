'use client'

import { GraduationCap, Users, Trophy, TrendingDown } from 'lucide-react'
import { useTrainingLeaderboard, useTrainingModules } from '@/hooks/useNextgenApi'
import type { DeveloperTrainingProfile, TrainingModuleRecord } from '@/types/nextgen'

export default function ComplianceTrainingDashboard() {
  const { data: leaderboard, loading: lbLoading, error: lbError, refetch: refetchLb } = useTrainingLeaderboard()
  const { data: modules, loading: modsLoading, error: modsError, refetch: refetchMods } = useTrainingModules()

  const loading = lbLoading || modsLoading
  const error = lbError || modsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
        </div>
        <div className="card h-48 animate-pulse bg-gray-100" />
        <div className="card h-48 animate-pulse bg-gray-100" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading Compliance Training: {error.message}</p>
        <button onClick={() => { refetchLb(); refetchMods(); }} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const lbEntries = leaderboard ?? []
  const avgScore = lbEntries.length > 0
    ? (lbEntries.reduce((sum, d) => sum + d.compliance_score, 0) / lbEntries.length).toFixed(1)
    : '—'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Continuous Compliance Training Copilot</h1>
        <p className="text-gray-500">Adaptive micro-trainings triggered by code violations</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Modules Available</p>
            <GraduationCap className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{modules?.length ?? 0}</p>
          <p className="mt-1 text-sm text-gray-500">Across all regulations</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Active Learners</p>
            <Users className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">{lbEntries.length}</p>
          <p className="mt-1 text-sm text-gray-500">On leaderboard</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Avg Score</p>
            <Trophy className="h-5 w-5 text-yellow-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-yellow-600">{avgScore}%</p>
          <p className="mt-1 text-sm text-gray-500">Team average</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Skill Levels</p>
            <TrendingDown className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{lbEntries.filter(d => d.skill_level === 'advanced').length}</p>
          <p className="mt-1 text-sm text-gray-500">Advanced developers</p>
        </div>
      </div>

      {/* Leaderboard */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Trophy className="h-5 w-5 text-yellow-500" />
          <h2 className="text-lg font-semibold text-gray-900">Leaderboard</h2>
        </div>
        {lbEntries.length === 0 ? (
          <p className="text-gray-500 text-sm">No leaderboard entries yet.</p>
        ) : (
          <div className="space-y-3">
            {lbEntries.map((dev: DeveloperTrainingProfile, i: number) => (
              <div key={dev.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold text-gray-400">#{i + 1}</span>
                  <div>
                    <p className="font-medium text-gray-900">{dev.name}</p>
                    <p className="text-sm text-gray-500">{dev.completed_modules.length} modules · {dev.skill_level}</p>
                  </div>
                </div>
                <span className="text-2xl font-bold text-blue-600">{dev.compliance_score}%</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modules */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <GraduationCap className="h-5 w-5 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-900">Training Modules</h2>
        </div>
        {!modules || modules.length === 0 ? (
          <p className="text-gray-500 text-sm">No training modules available yet.</p>
        ) : (
          <div className="space-y-3">
            {modules.map((mod: TrainingModuleRecord) => (
              <div key={mod.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-gray-900">{mod.title}</span>
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${mod.skill_level === 'beginner' ? 'text-green-700 bg-green-100' : mod.skill_level === 'intermediate' ? 'text-yellow-700 bg-yellow-100' : 'text-red-700 bg-red-100'}`}>
                    {mod.skill_level}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>{mod.regulation}</span>
                  <span>{mod.duration_minutes} min</span>
                  <span>{mod.format}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
