'use client'

import { FileText, BarChart3, AlertTriangle, CheckCircle } from 'lucide-react'
import { useBoardExecutiveSummary } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function BoardReportsDashboard() {
  const { data: summary, loading, error, refetch } = useBoardExecutiveSummary()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Board Reports</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Board Reports</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Board Reports: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Board Reports</h1>
        <p className="text-gray-500">AI-powered executive compliance reports for board presentations</p>
      </div>
      {summary && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard icon={<BarChart3 className="w-5 h-5 text-blue-500" />} title="Overall Score" value={`${summary.overall_score}`} subtitle={summary.overall_status} />
            <StatCard icon={<FileText className="w-5 h-5 text-green-500" />} title="Period" value={summary.period} subtitle={summary.title} />
            <StatCard icon={<AlertTriangle className="w-5 h-5 text-orange-500" />} title="Top Risks" value={String(summary.top_risks.length)} subtitle="Action items" />
            <StatCard icon={<CheckCircle className="w-5 h-5 text-purple-500" />} title="Highlights" value={String(summary.highlights.length)} subtitle="Key metrics" />
          </div>
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Executive Narrative</h2>
            <p className="text-gray-700">{summary.narrative}</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Compliance Highlights</h2>
              <div className="space-y-2">
                {summary.highlights.map((h, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="font-medium text-gray-700">{h.category}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">{h.score}</span>
                      <span className={`px-2 py-0.5 rounded text-xs ${h.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>{h.trend === 'up' ? '↑' : '↓'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Action Items</h2>
              {summary.action_items.length === 0 ? <p className="text-gray-500">No action items.</p> : (
                <ul className="space-y-2">
                  {summary.action_items.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
