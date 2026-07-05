'use client'

import { Download, CheckCircle, BarChart3, FileText } from 'lucide-react'
import { useExportJobs, useExportSummary } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ComplianceExportDashboard() {
  const { data: jobs, loading: jobsLoading, error: jobsError, refetch } = useExportJobs()
  const { data: summary, loading: summaryLoading, error: summaryError } = useExportSummary()

  const loading = jobsLoading || summaryLoading
  const error = jobsError || summaryError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Export</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Export</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Compliance Export: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Export</h1>
        <p className="text-gray-500">Export compliance reports to PDF, CSV, and other formats</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FileText className="w-5 h-5 text-blue-500" />} title="Total Exports" value={String(summary?.total_exports ?? 0)} subtitle="Export jobs run" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-500" />} title="Rows Exported" value={String(summary?.total_rows_exported ?? 0)} subtitle="Total records" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-orange-500" />} title="Schedules" value={String(summary?.active_schedules ?? 0)} subtitle="Active schedules" />
        <StatCard icon={<Download className="w-5 h-5 text-purple-500" />} title="Storage" value={`${((summary?.total_bytes_exported ?? 0) / 1048576).toFixed(1)} MB`} subtitle="Total exports size" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Export Jobs</h2>
        {!jobs || jobs.length === 0 ? (
          <p className="text-gray-500">No export jobs yet.</p>
        ) : (
          <div className="space-y-3">
            {jobs.slice(0, 10).map((job) => (
              <div key={job.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Download className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{job.data_type} · {job.format.toUpperCase()}</p>
                    <p className="text-sm text-gray-500">{job.row_count.toLocaleString()} rows · Created: {job.created_at ?? 'N/A'}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  job.status === 'completed' ? 'bg-green-100 text-green-700' :
                  job.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                  job.status === 'failed' ? 'bg-red-100 text-red-700' :
                  'bg-blue-100 text-blue-700'
                }`}>{job.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
