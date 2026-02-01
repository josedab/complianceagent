'use client'

import { useState, useMemo } from 'react'
import { Search, Code, CheckCircle, Clock, XCircle, Play, Eye, GitPullRequest } from 'lucide-react'
import { useComplianceActions, useUpdateAction } from '@/hooks/useApi'
import { ActionsSkeleton } from '@/components/ui/Skeleton'
import type { ComplianceAction, ActionStatus, ActionPriority } from '@/types'

const statusOptions = [
  { value: 'All', label: 'All Status' },
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'review', label: 'In Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'completed', label: 'Completed' },
]

const priorityOptions = [
  { value: 'All', label: 'All Priorities' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]

export default function ActionsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('All')
  const [selectedPriority, setSelectedPriority] = useState('All')
  const [selectedAction, setSelectedAction] = useState<ComplianceAction | null>(null)

  const { data: actions, loading, error, refetch } = useComplianceActions()
  const { updateAction, loading: updating } = useUpdateAction()

  const filteredActions = useMemo(() => {
    if (!actions) return []
    return actions.filter((action) => {
      const matchesSearch = 
        action.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        action.description.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesStatus = selectedStatus === 'All' || action.status === selectedStatus
      const matchesPriority = selectedPriority === 'All' || action.priority === selectedPriority
      return matchesSearch && matchesStatus && matchesPriority
    })
  }, [actions, searchQuery, selectedStatus, selectedPriority])

  const statusCounts = useMemo(() => ({
    pending: actions?.filter(a => a.status === 'pending' || a.status === 'review').length || 0,
    inProgress: actions?.filter(a => a.status === 'in_progress').length || 0,
    completed: actions?.filter(a => a.status === 'completed' || a.status === 'merged').length || 0,
  }), [actions])

  const handleApprove = async (id: string) => {
    try {
      await updateAction(id, { status: 'approved' })
      refetch()
    } catch (err) {
      console.error('Failed to approve action:', err)
    }
  }

  if (loading) {
    return <ActionsSkeleton />
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Compliance Actions</h1>
          <p className="text-gray-500">Review and manage compliance code changes</p>
        </div>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 text-sm">Unable to load from server.</p>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-yellow-50 border-yellow-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-yellow-800 text-sm font-medium">Pending Approval</p>
              <p className="text-3xl font-bold text-yellow-900">{statusCounts.pending}</p>
            </div>
            <Clock className="h-10 w-10 text-yellow-600" />
          </div>
        </div>
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-800 text-sm font-medium">In Progress</p>
              <p className="text-3xl font-bold text-blue-900">{statusCounts.inProgress}</p>
            </div>
            <Play className="h-10 w-10 text-blue-600" />
          </div>
        </div>
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-800 text-sm font-medium">Completed</p>
              <p className="text-3xl font-bold text-green-900">{statusCounts.completed}</p>
            </div>
            <CheckCircle className="h-10 w-10 text-green-600" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search actions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="flex gap-4">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {statusOptions.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {priorityOptions.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Actions List */}
      <div className="space-y-4">
        {filteredActions.map((action) => (
          <ActionCard 
            key={action.id} 
            action={action} 
            onView={() => setSelectedAction(action)}
            onApprove={() => handleApprove(action.id)}
            updating={updating}
          />
        ))}

        {filteredActions.length === 0 && (
          <div className="card text-center py-12">
            <Code className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No actions found matching your criteria</p>
          </div>
        )}
      </div>

      {/* Action Detail Modal */}
      {selectedAction && (
        <ActionDetailModal 
          action={selectedAction} 
          onClose={() => setSelectedAction(null)}
          onApprove={() => {
            handleApprove(selectedAction.id)
            setSelectedAction(null)
          }}
          updating={updating}
        />
      )}
    </div>
  )
}

function ActionCard({ 
  action, 
  onView, 
  onApprove,
  updating 
}: { 
  action: ComplianceAction
  onView: () => void
  onApprove: () => void
  updating: boolean
}) {
  const statusConfig: Record<ActionStatus, { label: string; class: string; icon: typeof Clock }> = {
    pending: { label: 'Pending', class: 'status-pending', icon: Clock },
    in_progress: { label: 'In Progress', class: 'bg-blue-100 text-blue-800', icon: Play },
    review: { label: 'In Review', class: 'bg-purple-100 text-purple-800', icon: Eye },
    approved: { label: 'Approved', class: 'bg-green-100 text-green-800', icon: CheckCircle },
    merged: { label: 'Merged', class: 'status-compliant', icon: GitPullRequest },
    completed: { label: 'Completed', class: 'status-compliant', icon: CheckCircle },
    rejected: { label: 'Rejected', class: 'status-non-compliant', icon: XCircle },
  }

  const priorityConfig: Record<ActionPriority, string> = {
    critical: 'bg-red-100 text-red-800',
    high: 'bg-orange-100 text-orange-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-gray-100 text-gray-800',
  }

  const status = statusConfig[action.status] || statusConfig.pending
  const StatusIcon = status.icon

  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <h3 className="text-lg font-semibold text-gray-900">{action.title}</h3>
            <span className={`status-badge ${priorityConfig[action.priority]}`}>
              {action.priority}
            </span>
            <span className={`status-badge ${status.class} flex items-center`}>
              <StatusIcon className="h-3 w-3 mr-1" />
              {status.label}
            </span>
          </div>
          <p className="text-gray-600 mb-3">{action.description}</p>
          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
            {action.affected_files.length > 0 && (
              <div className="flex items-center gap-1">
                <Code className="h-4 w-4" />
                <span>{action.affected_files.length} files</span>
              </div>
            )}
            {action.estimated_effort_hours && (
              <div>
                <span className="font-medium">Effort:</span> {action.estimated_effort_hours}h
              </div>
            )}
            {action.due_date && (
              <div>
                <span className="font-medium">Due:</span> {new Date(action.due_date).toLocaleDateString()}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onView} className="btn-secondary flex items-center gap-1">
            <Eye className="h-4 w-4" />
            View
          </button>
          {(action.status === 'pending' || action.status === 'review') && (
            <button 
              onClick={onApprove} 
              className="btn-primary"
              disabled={updating}
            >
              {updating ? 'Approving...' : 'Approve'}
            </button>
          )}
          {action.pr_url && (
            <a
              href={action.pr_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary flex items-center gap-1"
            >
              <GitPullRequest className="h-4 w-4" />
              PR
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

function ActionDetailModal({ 
  action, 
  onClose,
  onApprove,
  updating
}: { 
  action: ComplianceAction
  onClose: () => void
  onApprove: () => void
  updating: boolean
}) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900">{action.title}</h2>
        </div>
        
        <div className="p-6 space-y-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500 mb-1">Description</h3>
            <p className="text-gray-900">{action.description}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Status</h3>
              <p className="text-gray-900 capitalize">{action.status.replace('_', ' ')}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-1">Priority</h3>
              <p className="text-gray-900 capitalize">{action.priority}</p>
            </div>
            {action.estimated_effort_hours && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Estimated Effort</h3>
                <p className="text-gray-900">{action.estimated_effort_hours} hours</p>
              </div>
            )}
            {action.due_date && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Due Date</h3>
                <p className="text-gray-900">{new Date(action.due_date).toLocaleDateString()}</p>
              </div>
            )}
          </div>

          {action.affected_files.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Affected Files</h3>
              <ul className="bg-gray-50 rounded-lg p-3 space-y-1">
                {action.affected_files.map((file) => (
                  <li key={file} className="font-mono text-sm text-gray-700">{file}</li>
                ))}
              </ul>
            </div>
          )}

          {action.generated_code && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Generated Code Preview</h3>
              <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 text-sm overflow-x-auto">
                {action.generated_code.pr_suggestion?.body || 'Code preview not available'}
              </pre>
            </div>
          )}
        </div>

        <div className="p-6 border-t bg-gray-50 flex justify-end gap-3">
          <button onClick={onClose} className="btn-secondary">Close</button>
          {(action.status === 'pending' || action.status === 'review') && (
            <>
              <button className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg">Reject</button>
              <button 
                onClick={onApprove} 
                className="btn-primary"
                disabled={updating}
              >
                {updating ? 'Approving...' : 'Approve & Create PR'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
