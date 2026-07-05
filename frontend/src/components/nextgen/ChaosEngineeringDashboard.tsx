'use client'

import { Zap, Eye, AlertCircle, BarChart3 } from 'lucide-react'
import { useChaosExperiments, useChaosStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ChaosEngineeringDashboard() {
  const { data: experiments, loading: expLoading, error: expError, refetch } = useChaosExperiments()
  const { data: stats, loading: statsLoading, error: statsError } = useChaosStats()

  const loading = expLoading || statsLoading
  const error = expError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Chaos Engineering</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Chaos Engineering</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Chaos Engineering: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Chaos Engineering</h1>
        <p className="text-gray-500">Test compliance controls under failure conditions</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Zap className="w-5 h-5 text-blue-500" />} title="Experiments" value={String(stats?.total_experiments ?? 0)} subtitle={`${stats?.experiments_detected ?? 0} detected`} />
        <StatCard icon={<Eye className="w-5 h-5 text-green-500" />} title="Detection Rate" value={`${((stats?.detection_rate ?? 0) * 100).toFixed(1)}%`} subtitle="Controls validated" />
        <StatCard icon={<AlertCircle className="w-5 h-5 text-orange-500" />} title="Blind Spots" value={String(stats?.blind_spots_found ?? 0)} subtitle="Found" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-purple-500" />} title="Avg MTTR" value={`${((stats?.avg_mttr_seconds ?? 0) / 60).toFixed(1)}m`} subtitle="Mean time to remediate" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Experiments</h2>
        {!experiments || experiments.length === 0 ? (
          <p className="text-gray-500">No chaos experiments yet.</p>
        ) : (
          <div className="space-y-3">
            {experiments.map((exp) => (
              <div key={exp.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Zap className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{exp.name}</p>
                    <p className="text-sm text-gray-500">{exp.target_service} · {exp.experiment_type} · {exp.blast_radius}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  exp.status === 'completed' ? 'bg-green-100 text-green-700' :
                  exp.status === 'running' ? 'bg-blue-100 text-blue-700' :
                  'bg-gray-100 text-gray-700'
                }`}>{exp.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
