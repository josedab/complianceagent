'use client'

import { Gamepad2, Trophy, Play, Users } from 'lucide-react'
import { useGameScenarios, useGameLeaderboard } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function GameEngineDashboard() {
  const { data: scenarios, loading: scenLoading, error: scenError, refetch } = useGameScenarios()
  const { data: leaderboard, loading: lbLoading, error: lbError } = useGameLeaderboard()

  const loading = scenLoading || lbLoading
  const error = scenError || lbError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Game Engine</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Game Engine</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Compliance Game Engine: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const topXp = leaderboard && leaderboard.length > 0 ? leaderboard[0].total_xp : 0
  const avgXp = leaderboard && leaderboard.length > 0 ? Math.round(leaderboard.reduce((s, e) => s + e.total_xp, 0) / leaderboard.length) : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Game Engine</h1>
        <p className="text-gray-500">Gamified compliance training with scenarios and leaderboards</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Play className="w-5 h-5 text-blue-500" />} title="Scenarios" value={String(scenarios?.length ?? 0)} subtitle="Training scenarios" />
        <StatCard icon={<Users className="w-5 h-5 text-green-500" />} title="Players" value={String(leaderboard?.length ?? 0)} subtitle="Leaderboard entries" />
        <StatCard icon={<Trophy className="w-5 h-5 text-yellow-500" />} title="Top XP" value={String(topXp)} subtitle="Highest score" />
        <StatCard icon={<Gamepad2 className="w-5 h-5 text-purple-500" />} title="Avg XP" value={String(avgXp)} subtitle="Average score" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Scenarios</h2>
          {!scenarios || scenarios.length === 0 ? (
            <p className="text-gray-500">No scenarios available.</p>
          ) : (
            <div className="space-y-3">
              {scenarios.slice(0, 5).map((s) => (
                <div key={s.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{s.title}</p>
                    <p className="text-sm text-gray-500">{s.difficulty} · {s.frameworks.join(', ')}</p>
                  </div>
                  <span className="text-sm text-gray-600">{s.max_score} pts</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Leaderboard</h2>
          {!leaderboard || leaderboard.length === 0 ? (
            <p className="text-gray-500">No leaderboard entries yet.</p>
          ) : (
            <div className="space-y-3">
              {leaderboard.slice(0, 5).map((entry) => (
                <div key={entry.rank} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-bold ${entry.rank === 1 ? 'text-yellow-600' : entry.rank === 2 ? 'text-gray-500' : entry.rank === 3 ? 'text-orange-600' : 'text-gray-400'}`}>#{entry.rank}</span>
                    <div>
                      <p className="font-medium text-gray-900">{entry.display_name}</p>
                      <p className="text-sm text-gray-500">{entry.scenarios_completed} scenarios · Level {entry.level}</p>
                    </div>
                  </div>
                  <span className="font-semibold text-gray-900">{entry.total_xp} XP</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
