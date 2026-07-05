'use client'

import { Bot, AlertTriangle, CheckCircle, FileText } from 'lucide-react'
import { useComplianceCopilotViolations } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ComplianceCopilotDashboard() {
  const { data: violations, loading, error, refetch } = useComplianceCopilotViolations()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Copilot</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Copilot</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Compliance Copilot: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const critical = violations?.filter(v => v.severity === 'critical') ?? []
  const high = violations?.filter(v => v.severity === 'high') ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Copilot</h1>
        <p className="text-gray-500">AI-powered compliance violation detection and remediation suggestions</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Bot className="w-5 h-5 text-blue-500" />} title="Violations" value={String(violations?.length ?? 0)} subtitle="Total violations" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-red-500" />} title="Critical" value={String(critical.length)} subtitle="Critical severity" />
        <StatCard icon={<FileText className="w-5 h-5 text-orange-500" />} title="High" value={String(high.length)} subtitle="High severity" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-500" />} title="Frameworks" value={String(violations ? new Set(violations.map(v => v.framework)).size : 0)} subtitle="Covered frameworks" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Violations</h2>
        {!violations || violations.length === 0 ? (
          <p className="text-gray-500">No compliance violations detected.</p>
        ) : (
          <div className="space-y-3">
            {violations.slice(0, 10).map((v) => (
              <div key={v.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <AlertTriangle className={`w-5 h-5 ${v.severity === 'critical' ? 'text-red-500' : v.severity === 'high' ? 'text-orange-500' : 'text-yellow-500'}`} />
                  <div>
                    <p className="font-medium text-gray-900">{v.rule_id}</p>
                    <p className="text-sm text-gray-500">{v.file_path}:{v.line_start} · {v.framework} · {v.article_ref}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  v.severity === 'critical' ? 'bg-red-100 text-red-700' :
                  v.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                  'bg-yellow-100 text-yellow-700'
                }`}>{v.severity}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
