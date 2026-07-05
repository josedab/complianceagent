'use client'

import { useState } from 'react'
import { FileCheck, Shield, Clock, CheckCircle } from 'lucide-react'
import { useAuditFrameworks, useGapAnalysis, useReadinessReport } from '@/hooks/useNextgenApi'
import type { GapAnalysis, ReadinessReport } from '@/types/nextgen'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm text-gray-500">{title}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function AuditAutopilotDashboard() {
  const { data: frameworks, loading, error, refetch } = useAuditFrameworks()
  const { mutate: runGapAnalysis, loading: gapLoading } = useGapAnalysis()
  const { mutate: runReadinessReport, loading: readinessLoading } = useReadinessReport()
  const [results, setResults] = useState<Record<string, { gap?: GapAnalysis; readiness?: ReadinessReport }>>({})
  const [actionError, setActionError] = useState<string | null>(null)

  async function handleRunGapAnalysis(framework: string) {
    setActionError(null)
    try {
      const gap = await runGapAnalysis(framework)
      setResults(prev => ({ ...prev, [framework]: { ...prev[framework], gap } }))
    } catch {
      setActionError(`Failed to run gap analysis for ${framework}`)
    }
  }

  async function handleRunReadinessReport(framework: string) {
    setActionError(null)
    try {
      const readiness = await runReadinessReport(framework)
      setResults(prev => ({ ...prev, [framework]: { ...prev[framework], readiness } }))
    } catch {
      setActionError(`Failed to generate readiness report for ${framework}`)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}
        </div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Preparation Autopilot</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading audit frameworks: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const items = frameworks || []
  const totalControls = items.reduce((sum, f) => sum + f.control_count, 0)
  const analyzedCount = Object.keys(results).length
  const avgReadiness = analyzedCount > 0
    ? (Object.values(results).reduce((sum, r) => sum + (r.gap?.readiness_score ?? r.readiness?.overall_readiness ?? 0), 0) / analyzedCount).toFixed(0)
    : null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Preparation Autopilot</h1>
        <p className="text-gray-500">Automated audit preparation and evidence collection</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FileCheck className="h-5 w-5 text-blue-600" />} title="Frameworks" value={String(items.length)} subtitle="Supported" />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Controls" value={String(totalControls)} subtitle="Across all frameworks" />
        <StatCard icon={<Clock className="h-5 w-5 text-purple-600" />} title="Readiness" value={avgReadiness !== null ? `${avgReadiness}%` : 'N/A'} subtitle="Avg across analyzed frameworks" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-orange-600" />} title="Analyzed" value={String(analyzedCount)} subtitle="Frameworks assessed" />
      </div>
      {actionError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">{actionError}</div>
      )}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Supported Audit Frameworks</h2>
        {items.length === 0 ? (
          <p className="text-gray-500 text-sm">No audit frameworks available.</p>
        ) : (
          <div className="space-y-3">
            {items.map((item) => {
              const result = results[item.framework]
              return (
                <div key={item.framework} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
                  <div>
                    <span className="font-medium text-gray-900 uppercase">{item.framework}</span>
                    <p className="text-xs text-gray-500">
                      {item.control_count} controls
                      {result?.gap && ` · readiness ${result.gap.readiness_score}%`}
                      {result?.readiness && ` · prep ${result.readiness.estimated_prep_weeks}w`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleRunGapAnalysis(item.framework)}
                      disabled={gapLoading}
                      className="px-3 py-1 bg-white border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Run Gap Analysis
                    </button>
                    <button
                      onClick={() => handleRunReadinessReport(item.framework)}
                      disabled={readinessLoading}
                      className="px-3 py-1 bg-white border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                    >
                      Readiness Report
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
