'use client'

import { Award, TrendingUp, CheckCircle, Clock } from 'lucide-react'
import { useCertJourneys } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function CertAutopilotDashboard() {
  const { data: journeys, loading, error, refetch } = useCertJourneys()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Certification Autopilot</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Certification Autopilot</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Cert Autopilot: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const avgProgress = journeys && journeys.length > 0
    ? journeys.reduce((sum, j) => sum + j.progress_percent, 0) / journeys.length
    : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Certification Autopilot</h1>
        <p className="text-gray-500">Automate SOC2, ISO27001, and HIPAA certification journeys</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Award className="w-5 h-5 text-blue-500" />} title="Active Journeys" value={String(journeys?.length ?? 0)} subtitle="Certification journeys" />
        <StatCard icon={<TrendingUp className="w-5 h-5 text-green-500" />} title="Avg Progress" value={`${avgProgress.toFixed(1)}%`} subtitle="Across all journeys" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-purple-500" />} title="Frameworks" value={String(new Set(journeys?.map(j => j.framework) ?? []).size)} subtitle="Unique frameworks" />
        <StatCard icon={<Clock className="w-5 h-5 text-orange-500" />} title="Phases" value={String(new Set(journeys?.map(j => j.current_phase) ?? []).size)} subtitle="Active phases" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Certification Journeys</h2>
        {!journeys || journeys.length === 0 ? (
          <p className="text-gray-500">No certification journeys started yet.</p>
        ) : (
          <div className="space-y-3">
            {journeys.map((journey, idx) => (
              <div key={journey.id ?? idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Award className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{journey.framework}</p>
                    <p className="text-sm text-gray-500">Phase: {journey.current_phase} · Progress: {journey.progress_percent.toFixed(1)}%</p>
                  </div>
                </div>
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${journey.progress_percent}%` }} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
