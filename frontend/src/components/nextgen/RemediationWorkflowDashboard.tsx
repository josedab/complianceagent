'use client'

import { GitBranch, CheckCircle, RotateCcw, BarChart3, Clock, AlertTriangle } from 'lucide-react'
import { useRemediationAnalytics } from '@/hooks/useNextgenApi'
import type { RemediationAnalytics } from '@/types/nextgen'

const MOCK_ANALYTICS: RemediationAnalytics = {
  total_workflows: 42,
  completed_workflows: 28,
  in_progress_workflows: 8,
  failed_workflows: 4,
  rolled_back_workflows: 2,
  avg_time_to_remediate_hours: 4.5,
  fix_success_rate: 0.867,
  auto_fix_rate: 0.65,
  top_violation_types: [
    { type: 'data_privacy', count: 12 },
    { type: 'encryption', count: 8 },
    { type: 'access_control', count: 6 },
    { type: 'audit_logging', count: 5 },
    { type: 'data_retention', count: 3 },
  ],
  monthly_trend: [
    { month: 'Oct', completed: 5, failed: 1 },
    { month: 'Nov', completed: 7, failed: 2 },
    { month: 'Dec', completed: 6, failed: 1 },
    { month: 'Jan', completed: 8, failed: 2 },
    { month: 'Feb', completed: 10, failed: 1 },
  ],
}

export default function RemediationWorkflowDashboard() {
  const { data: liveAnalytics } = useRemediationAnalytics()
  const analytics = liveAnalytics || MOCK_ANALYTICS

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Remediation Workflows</h1>
        <p className="text-gray-500">Automated compliance fix workflows with approval chains and rollback</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Total Workflows</p>
            <GitBranch className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{analytics.total_workflows}</p>
          <p className="mt-1 text-sm text-gray-500">{analytics.in_progress_workflows} in progress</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Success Rate</p>
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{Math.round(analytics.fix_success_rate * 100)}%</p>
          <p className="mt-1 text-sm text-gray-500">{analytics.completed_workflows} completed</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Avg Time</p>
            <Clock className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">{analytics.avg_time_to_remediate_hours}h</p>
          <p className="mt-1 text-sm text-gray-500">To remediate</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Rollbacks</p>
            <RotateCcw className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{analytics.rolled_back_workflows}</p>
          <p className="mt-1 text-sm text-gray-500">{analytics.failed_workflows} failed</p>
        </div>
      </div>

      {/* Violation Types */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-5 w-5 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-900">Top Violation Types</h2>
        </div>
        <div className="space-y-3">
          {analytics.top_violation_types.map((v: Record<string, unknown>, i: number) => {
            const max = Math.max(...analytics.top_violation_types.map((t: Record<string, unknown>) => t.count as number))
            const pct = Math.round(((v.count as number) / max) * 100)
            return (
              <div key={i} className="flex items-center gap-4">
                <span className="w-36 text-sm font-medium text-gray-700 capitalize">{(v.type as string).replace('_', ' ')}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-3">
                  <div className="bg-primary-600 h-3 rounded-full transition-all" style={{ width: `${pct}%` }} />
                </div>
                <span className="text-sm font-medium text-gray-600 w-8 text-right">{v.count as number}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Monthly Trend */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          <h2 className="text-lg font-semibold text-gray-900">Monthly Trend</h2>
        </div>
        <div className="grid grid-cols-5 gap-2">
          {analytics.monthly_trend.map((m: Record<string, unknown>, i: number) => (
            <div key={i} className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-500">{m.month as string}</p>
              <p className="text-lg font-bold text-green-600">{m.completed as number}</p>
              <p className="text-xs text-gray-400">completed</p>
              {(m.failed as number) > 0 && (
                <p className="text-xs text-red-500 mt-1">{m.failed as number} failed</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
