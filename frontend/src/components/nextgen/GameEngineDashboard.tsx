'use client'

import { useState } from 'react'
import { Gamepad2, Trophy, Clock, Target, Zap, ChevronRight } from 'lucide-react'

type Difficulty = 'tutorial' | 'easy' | 'medium' | 'hard' | 'expert'
type Category = 'data_breach' | 'audit_response' | 'ransomware' | 'api_data_leak' | 'vendor_violation'

interface GameScenario {
  id: string
  title: string
  description: string
  category: Category
  difficulty: Difficulty
  estimatedMinutes: number
  maxScore: number
  decisionsCount: number
  frameworks: string[]
}

interface LeaderboardEntry {
  displayName: string
  organization: string
  totalXp: number
  level: number
  scenariosCompleted: number
  accuracyRate: number
  rank: number
}

const difficultyConfig: Record<Difficulty, { label: string; color: string }> = {
  tutorial: { label: 'Tutorial', color: 'bg-gray-100 text-gray-700' },
  easy: { label: 'Easy', color: 'bg-green-100 text-green-700' },
  medium: { label: 'Medium', color: 'bg-yellow-100 text-yellow-700' },
  hard: { label: 'Hard', color: 'bg-orange-100 text-orange-700' },
  expert: { label: 'Expert', color: 'bg-red-100 text-red-700' },
}

const categoryConfig: Record<Category, { label: string; icon: string }> = {
  data_breach: { label: 'Data Breach', icon: '🔓' },
  audit_response: { label: 'Audit Response', icon: '📋' },
  ransomware: { label: 'Ransomware', icon: '🔒' },
  api_data_leak: { label: 'API Data Leak', icon: '🌐' },
  vendor_violation: { label: 'Vendor Violation', icon: '🤝' },
}

const MOCK_SCENARIOS: GameScenario[] = [
  { id: 'gdpr-breach-response', title: 'GDPR Data Breach Response', description: 'Navigate the 72-hour breach notification process after a production database exposure.',
    category: 'data_breach', difficulty: 'medium', estimatedMinutes: 20, maxScore: 100, decisionsCount: 3, frameworks: ['GDPR'] },
  { id: 'hipaa-audit-prep', title: 'HIPAA Audit Preparation', description: 'Prepare documentation and evidence for an OCR HIPAA compliance audit.',
    category: 'audit_response', difficulty: 'hard', estimatedMinutes: 25, maxScore: 120, decisionsCount: 2, frameworks: ['HIPAA'] },
  { id: 'ransomware-response', title: 'Ransomware Attack Response', description: 'Navigate incident response while maintaining multi-framework compliance.',
    category: 'ransomware', difficulty: 'expert', estimatedMinutes: 30, maxScore: 150, decisionsCount: 2, frameworks: ['GDPR', 'HIPAA', 'PCI-DSS'] },
  { id: 'api-data-leak', title: 'API Data Leak Investigation', description: 'Investigate and remediate verbose error messages leaking user data.',
    category: 'api_data_leak', difficulty: 'easy', estimatedMinutes: 15, maxScore: 80, decisionsCount: 1, frameworks: ['GDPR', 'SOC 2'] },
  { id: 'vendor-violation', title: 'Third-Party Vendor Violation', description: 'Navigate shared responsibility after a cloud vendor breach.',
    category: 'vendor_violation', difficulty: 'medium', estimatedMinutes: 20, maxScore: 100, decisionsCount: 1, frameworks: ['GDPR', 'SOC 2'] },
]

const MOCK_LEADERBOARD: LeaderboardEntry[] = [
  { displayName: 'ComplianceNinja', organization: 'Acme Corp', totalXp: 2450, level: 12, scenariosCompleted: 8, accuracyRate: 0.92, rank: 1 },
  { displayName: 'RegTechPro', organization: 'FinanceHQ', totalXp: 1890, level: 9, scenariosCompleted: 6, accuracyRate: 0.85, rank: 2 },
  { displayName: 'PrivacyChampion', organization: 'HealthCo', totalXp: 1520, level: 7, scenariosCompleted: 5, accuracyRate: 0.88, rank: 3 },
  { displayName: 'AuditAce', organization: 'TechStartup', totalXp: 980, level: 5, scenariosCompleted: 3, accuracyRate: 0.78, rank: 4 },
]

const MOCK_ACHIEVEMENTS = [
  { id: 'gdpr-guardian', name: 'GDPR Guardian', description: 'Complete all GDPR scenarios', icon: '🛡️', tier: 'gold' },
  { id: 'breach-responder', name: 'Breach Responder', description: 'Score 90%+ on a breach scenario', icon: '🚨', tier: 'silver' },
  { id: 'speed-demon', name: 'Speed Demon', description: 'Complete a scenario in under 5 minutes', icon: '⚡', tier: 'bronze' },
  { id: 'perfect-score', name: 'Perfect Score', description: 'Achieve 100% on any scenario', icon: '💎', tier: 'platinum' },
]

export default function GameEngineDashboard() {
  const [activeTab, setActiveTab] = useState<'scenarios' | 'leaderboard' | 'achievements'>('scenarios')
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all')

  const filteredScenarios = difficultyFilter === 'all' ? MOCK_SCENARIOS : MOCK_SCENARIOS.filter(s => s.difficulty === difficultyFilter)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Gamepad2 className="h-7 w-7 text-indigo-600" /> Compliance Game Engine</h1>
          <p className="text-gray-500 mt-1">Gamified compliance training with scenario-based challenges</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500">Your Level</div>
          <div className="text-2xl font-bold text-indigo-600">7</div>
          <div className="text-xs text-gray-400">1,520 XP</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        {(['scenarios', 'leaderboard', 'achievements'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === tab ? 'bg-white shadow text-indigo-600' : 'text-gray-600 hover:text-gray-900'}`}>
            {tab === 'scenarios' ? '🎮 Scenarios' : tab === 'leaderboard' ? '🏆 Leaderboard' : '🏅 Achievements'}
          </button>
        ))}
      </div>

      {activeTab === 'scenarios' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            {['all', 'easy', 'medium', 'hard', 'expert'].map(d => (
              <button key={d} onClick={() => setDifficultyFilter(d)}
                className={`px-3 py-1 rounded-full text-sm ${difficultyFilter === d ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700'}`}>
                {d.charAt(0).toUpperCase() + d.slice(1)}
              </button>
            ))}
          </div>
          {filteredScenarios.map(scenario => {
            const cat = categoryConfig[scenario.category]
            const diff = difficultyConfig[scenario.difficulty]
            return (
              <div key={scenario.id} className="bg-white rounded-lg border p-5 hover:shadow-md transition-shadow cursor-pointer">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{cat.icon}</span>
                      <span className="text-xs text-gray-500">{cat.label}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${diff.color}`}>{diff.label}</span>
                    </div>
                    <h3 className="text-lg font-semibold">{scenario.title}</h3>
                    <p className="text-gray-600 text-sm mt-1">{scenario.description}</p>
                    <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{scenario.estimatedMinutes}m</span>
                      <span className="flex items-center gap-1"><Target className="h-3 w-3" />{scenario.maxScore} pts</span>
                      <span className="flex items-center gap-1"><Zap className="h-3 w-3" />{scenario.decisionsCount} decisions</span>
                      {scenario.frameworks.map(fw => (
                        <span key={fw} className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded">{fw}</span>
                      ))}
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400 mt-2" />
                </div>
              </div>
            )
          })}
        </div>
      )}

      {activeTab === 'leaderboard' && (
        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b"><h3 className="font-semibold flex items-center gap-2"><Trophy className="h-5 w-5 text-yellow-500" /> Global Leaderboard</h3></div>
          <div className="divide-y">
            {MOCK_LEADERBOARD.map(entry => (
              <div key={entry.rank} className="p-4 flex items-center gap-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${entry.rank === 1 ? 'bg-yellow-100 text-yellow-700' : entry.rank === 2 ? 'bg-gray-100 text-gray-700' : entry.rank === 3 ? 'bg-orange-100 text-orange-700' : 'bg-gray-50 text-gray-500'}`}>
                  {entry.rank}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{entry.displayName}</div>
                  <div className="text-sm text-gray-500">{entry.organization}</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-indigo-600">{entry.totalXp.toLocaleString()} XP</div>
                  <div className="text-xs text-gray-500">Level {entry.level} · {entry.scenariosCompleted} completed · {(entry.accuracyRate * 100).toFixed(0)}% accuracy</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'achievements' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {MOCK_ACHIEVEMENTS.map(ach => (
            <div key={ach.id} className="bg-white rounded-lg border p-4 flex items-center gap-4">
              <div className="text-3xl">{ach.icon}</div>
              <div>
                <div className="font-semibold">{ach.name}</div>
                <div className="text-sm text-gray-500">{ach.description}</div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${ach.tier === 'platinum' ? 'bg-purple-100 text-purple-700' : ach.tier === 'gold' ? 'bg-yellow-100 text-yellow-700' : ach.tier === 'silver' ? 'bg-gray-100 text-gray-700' : 'bg-orange-100 text-orange-700'}`}>
                  {ach.tier.charAt(0).toUpperCase() + ach.tier.slice(1)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
