'use client'

import { CheckCircle, AlertTriangle, Clock, FileText, TrendingUp, BarChart3, PieChart as PieChartIcon } from 'lucide-react'
import { useDashboardStats } from '@/hooks/useApi'
import { DashboardSkeleton } from '@/components/ui/Skeleton'
import {
  ComplianceTrendChart,
  RiskDistributionChart,
  FrameworkComparisonChart,
  generateTrendData,
  generateRiskData,
  generateFrameworkData,
} from '@/components/dashboard/Charts'
import type { FrameworkStatus, RecentActivity, UpcomingDeadline, ComplianceStatus } from '@/types'

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`
  return date.toLocaleDateString()
}

function statusToDisplay(status: ComplianceStatus): string {
  const map: Record<ComplianceStatus, string> = {
    COMPLIANT: 'compliant',
    PARTIAL_COMPLIANCE: 'partial',
    NON_COMPLIANT: 'non-compliant',
    NOT_APPLICABLE: 'n/a',
    PENDING_REVIEW: 'pending',
  }
  return map[status] || 'pending'
}

export default function DashboardPage() {
  const { stats, frameworkStatuses, recentActivity, deadlines, loading, error } = useDashboardStats()

  if (loading) {
    return <DashboardSkeleton />
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading dashboard: {error.message}</p>
        <p className="text-sm text-red-600 mt-1">Using fallback data for demonstration.</p>
      </div>
    )
  }

  const complianceStats = stats || {
    overall_score: 87,
    compliant: 42,
    partial: 8,
    non_compliant: 3,
    pending: 5,
    trend_percentage: 2.3,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Dashboard</h1>
        <p className="text-gray-500">Overview of your regulatory compliance status</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Overall Compliance"
          value={`${complianceStats.overall_score}%`}
          icon={<TrendingUp className="h-5 w-5 text-green-600" />}
          trend={`+${complianceStats.trend_percentage || 2.3}% from last month`}
          color="green"
        />
        <StatCard
          title="Compliant Requirements"
          value={complianceStats.compliant.toString()}
          icon={<CheckCircle className="h-5 w-5 text-green-600" />}
          subtitle={`of ${complianceStats.compliant + complianceStats.partial + complianceStats.non_compliant + complianceStats.pending} total`}
          color="green"
        />
        <StatCard
          title="Action Required"
          value={(complianceStats.partial + complianceStats.non_compliant).toString()}
          icon={<AlertTriangle className="h-5 w-5 text-yellow-600" />}
          subtitle={`${complianceStats.partial} partial, ${complianceStats.non_compliant} non-compliant`}
          color="yellow"
        />
        <StatCard
          title="Pending Review"
          value={complianceStats.pending.toString()}
          icon={<Clock className="h-5 w-5 text-gray-600" />}
          subtitle="Awaiting human review"
          color="gray"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Compliance Trend */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-5 w-5 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">Compliance Trend</h2>
          </div>
          <ComplianceTrendChart data={generateTrendData()} />
        </div>

        {/* Risk Distribution */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <PieChartIcon className="h-5 w-5 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">Risk Distribution</h2>
          </div>
          <RiskDistributionChart data={generateRiskData()} />
        </div>
      </div>

      {/* Framework Comparison */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Framework Compliance Comparison</h2>
        </div>
        <FrameworkComparisonChart data={generateFrameworkData()} />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Framework Status */}
        <div className="lg:col-span-2 card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Framework Compliance</h2>
          <div className="space-y-4">
            {frameworkStatuses.length > 0 ? (
              frameworkStatuses.map((framework) => (
                <FrameworkRow key={framework.framework} framework={framework} />
              ))
            ) : (
              <p className="text-gray-500 text-sm">No frameworks configured yet.</p>
            )}
          </div>
        </div>

        {/* Upcoming Deadlines */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Deadlines</h2>
          <div className="space-y-4">
            {deadlines.length > 0 ? (
              deadlines.map((deadline) => (
                <DeadlineRow key={deadline.regulation_id} deadline={deadline} />
              ))
            ) : (
              <p className="text-gray-500 text-sm">No upcoming deadlines.</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-4">
          {recentActivity.length > 0 ? (
            recentActivity.map((activity) => (
              <ActivityItem key={activity.id} activity={activity} />
            ))
          ) : (
            <p className="text-gray-500 text-sm">No recent activity.</p>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  title,
  value,
  icon,
  trend,
  subtitle,
}: {
  title: string
  value: string
  icon: React.ReactNode
  trend?: string
  subtitle?: string
  color: 'green' | 'yellow' | 'red' | 'gray'
}) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        {icon}
      </div>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
      {trend && <p className="mt-1 text-sm text-green-600">{trend}</p>}
      {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
    </div>
  )
}

function FrameworkRow({ framework }: { framework: FrameworkStatus }) {
  const statusColors: Record<string, string> = {
    COMPLIANT: 'bg-green-500',
    PARTIAL_COMPLIANCE: 'bg-yellow-500',
    NON_COMPLIANT: 'bg-red-500',
    NOT_APPLICABLE: 'bg-gray-300',
    PENDING_REVIEW: 'bg-gray-300',
  }

  const displayStatus = statusToDisplay(framework.status)

  return (
    <div className="flex items-center gap-4">
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="font-medium text-gray-900">{framework.name}</span>
          <span className="text-sm text-gray-500">{framework.score}%</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full ${statusColors[framework.status] || 'bg-gray-300'} transition-all`}
            style={{ width: `${framework.score}%` }}
          />
        </div>
      </div>
      <span
        className={`status-badge ${
          displayStatus === 'compliant'
            ? 'status-compliant'
            : displayStatus === 'partial'
            ? 'status-partial'
            : 'status-pending'
        }`}
      >
        {displayStatus}
      </span>
    </div>
  )
}

function DeadlineRow({ deadline }: { deadline: UpcomingDeadline }) {
  const priorityColors: Record<string, string> = {
    critical: 'text-red-600',
    high: 'text-orange-600',
    medium: 'text-yellow-600',
    low: 'text-gray-600',
  }

  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium text-gray-900">{deadline.regulation_name}</p>
        <p className="text-sm text-gray-500">
          {new Date(deadline.effective_date).toLocaleDateString('en-US', {
            month: 'short',
            year: 'numeric',
          })}
        </p>
      </div>
      <span className={`text-sm font-medium ${priorityColors[deadline.priority] || 'text-gray-700'}`}>
        {deadline.days_remaining} days
      </span>
    </div>
  )
}

function ActivityItem({ activity }: { activity: RecentActivity }) {
  const icons: Record<string, React.ReactNode> = {
    regulation_detected: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
    requirement_extracted: <FileText className="h-5 w-5 text-blue-500" />,
    pr_merged: <CheckCircle className="h-5 w-5 text-green-500" />,
    pr_created: <FileText className="h-5 w-5 text-purple-500" />,
    mapping_created: <FileText className="h-5 w-5 text-blue-500" />,
    code_generated: <FileText className="h-5 w-5 text-indigo-500" />,
    action_created: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
    action_approved: <CheckCircle className="h-5 w-5 text-green-500" />,
  }

  return (
    <div className="flex gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors">
      <div className="flex-shrink-0">
        {icons[activity.type] || <FileText className="h-5 w-5 text-gray-500" />}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-gray-900">{activity.title}</p>
        <p className="text-sm text-gray-500 truncate">{activity.description}</p>
      </div>
      <span className="text-sm text-gray-400 whitespace-nowrap">
        {formatTimeAgo(activity.timestamp)}
      </span>
    </div>
  )
}
