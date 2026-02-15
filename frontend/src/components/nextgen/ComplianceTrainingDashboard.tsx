'use client'

import { GraduationCap, Users, Trophy, TrendingDown } from 'lucide-react'
import { useTrainingLeaderboard } from '@/hooks/useNextgenApi'
import type { DeveloperTrainingProfile } from '@/types/nextgen'

interface LeaderboardEntry extends DeveloperTrainingProfile {
  score: number;
  modules_completed: number;
  violations_fixed: number;
  streak_days: number;
}

const MOCK_LEADERBOARD: LeaderboardEntry[] = [
  { id: 'dev1', developer_id: 'dev1', name: 'Alice Chen', skill_level: 'advanced', completed_modules: [], compliance_score: 95, strengths: [], weaknesses: [], score: 95, modules_completed: 16, violations_fixed: 24, streak_days: 14 },
  { id: 'dev2', developer_id: 'dev2', name: 'Bob Martinez', skill_level: 'intermediate', completed_modules: [], compliance_score: 88, strengths: [], weaknesses: [], score: 88, modules_completed: 14, violations_fixed: 19, streak_days: 8 },
  { id: 'dev3', developer_id: 'dev3', name: 'Carol Singh', skill_level: 'intermediate', completed_modules: [], compliance_score: 82, strengths: [], weaknesses: [], score: 82, modules_completed: 12, violations_fixed: 15, streak_days: 21 },
  { id: 'dev4', developer_id: 'dev4', name: 'David Kim', skill_level: 'beginner', completed_modules: [], compliance_score: 76, strengths: [], weaknesses: [], score: 76, modules_completed: 10, violations_fixed: 11, streak_days: 5 },
  { id: 'dev5', developer_id: 'dev5', name: 'Eva Johnson', skill_level: 'beginner', completed_modules: [], compliance_score: 71, strengths: [], weaknesses: [], score: 71, modules_completed: 8, violations_fixed: 8, streak_days: 3 },
]

const MOCK_MODULES = [
  { id: 'm1', title: 'GDPR Data Subject Rights', regulation: 'GDPR', difficulty: 'intermediate', duration_min: 15, completions: 38 },
  { id: 'm2', title: 'SOC 2 Access Controls', regulation: 'SOC2', difficulty: 'advanced', duration_min: 25, completions: 22 },
  { id: 'm3', title: 'HIPAA PHI Handling', regulation: 'HIPAA', difficulty: 'beginner', duration_min: 10, completions: 41 },
  { id: 'm4', title: 'PCI DSS Encryption Standards', regulation: 'PCI-DSS', difficulty: 'intermediate', duration_min: 20, completions: 29 },
]

export default function ComplianceTrainingDashboard() {
  const { data: liveLeaderboard } = useTrainingLeaderboard()

  const leaderboard = (liveLeaderboard as LeaderboardEntry[] | null) || MOCK_LEADERBOARD
  const avgScore = (leaderboard.reduce((sum, d) => sum + d.score, 0) / leaderboard.length).toFixed(1)

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
          <p className="mt-2 text-3xl font-bold text-gray-900">18</p>
          <p className="mt-1 text-sm text-gray-500">Across all regulations</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Active Learners</p>
            <Users className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">42</p>
          <p className="mt-1 text-sm text-gray-500">This month</p>
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
            <p className="text-sm font-medium text-gray-500">Violation Reduction</p>
            <TrendingDown className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">67%</p>
          <p className="mt-1 text-sm text-gray-500">Since training started</p>
        </div>
      </div>

      {/* Leaderboard */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Trophy className="h-5 w-5 text-yellow-500" />
          <h2 className="text-lg font-semibold text-gray-900">Leaderboard</h2>
        </div>
        <div className="space-y-3">
          {leaderboard.map((dev, i) => (
            <div key={dev.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-lg font-bold text-gray-400">#{i + 1}</span>
                <div>
                  <p className="font-medium text-gray-900">{dev.name}</p>
                  <p className="text-sm text-gray-500">{dev.modules_completed} modules · {dev.violations_fixed} fixes · {dev.streak_days}d streak</p>
                </div>
              </div>
              <span className="text-2xl font-bold text-blue-600">{dev.score}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* Modules */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <GraduationCap className="h-5 w-5 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-900">Training Modules</h2>
        </div>
        <div className="space-y-3">
          {MOCK_MODULES.map(mod => (
            <div key={mod.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900">{mod.title}</span>
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${mod.difficulty === 'beginner' ? 'text-green-700 bg-green-100' : mod.difficulty === 'intermediate' ? 'text-yellow-700 bg-yellow-100' : 'text-red-700 bg-red-100'}`}>
                  {mod.difficulty}
                </span>
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>{mod.regulation}</span>
                <span>{mod.duration_min} min</span>
                <span>{mod.completions} completions</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
