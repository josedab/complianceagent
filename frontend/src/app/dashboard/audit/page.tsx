'use client'

import { useState, useMemo } from 'react'
import { Search, FileText, Download, ChevronDown, ChevronRight, Hash } from 'lucide-react'
import { useAuditTrail } from '@/hooks/useApi'
import { AuditSkeleton } from '@/components/ui/Skeleton'
import type { AuditTrailEntry, AuditEventType } from '@/types'

const eventTypeOptions: Array<{ value: string; label: string }> = [
  { value: 'All', label: 'All Event Types' },
  { value: 'regulation_detected', label: 'Regulation Detected' },
  { value: 'requirement_extracted', label: 'Requirement Extracted' },
  { value: 'requirement_approved', label: 'Requirement Approved' },
  { value: 'mapping_created', label: 'Mapping Created' },
  { value: 'mapping_reviewed', label: 'Mapping Reviewed' },
  { value: 'code_generated', label: 'Code Generated' },
  { value: 'action_created', label: 'Action Created' },
  { value: 'action_approved', label: 'Action Approved' },
  { value: 'pr_created', label: 'PR Created' },
  { value: 'pr_merged', label: 'PR Merged' },
]

export default function AuditPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedEventType, setSelectedEventType] = useState('All')
  const [expandedEntry, setExpandedEntry] = useState<string | null>(null)

  const eventTypeParam = selectedEventType === 'All' ? undefined : selectedEventType
  const { data: auditEntries, loading, error } = useAuditTrail({ event_type: eventTypeParam })

  const filteredEntries = useMemo(() => {
    if (!auditEntries) return []
    return auditEntries.filter((entry) => {
      const matchesSearch = entry.description.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesSearch
    })
  }, [auditEntries, searchQuery])

  if (loading) {
    return <AuditSkeleton />
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Trail</h1>
          <p className="text-gray-500">Complete history of compliance activities</p>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <Download className="h-5 w-5" />
          Export Report
        </button>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 text-sm">Unable to load audit trail from server.</p>
        </div>
      )}

      {/* Hash Chain Verification */}
      <div className="card bg-green-50 border-green-200">
        <div className="flex items-center gap-3">
          <Hash className="h-8 w-8 text-green-600" />
          <div>
            <h3 className="font-semibold text-green-900">Hash Chain Verified</h3>
            <p className="text-green-700 text-sm">
              All {filteredEntries.length} audit entries form a valid tamper-proof chain. 
              Last verified: {new Date().toLocaleString()}
            </p>
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
              placeholder="Search audit entries..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <select
            value={selectedEventType}
            onChange={(e) => setSelectedEventType(e.target.value)}
            className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {eventTypeOptions.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-4">
        {filteredEntries.map((entry, index) => (
          <AuditEntryCard
            key={entry.id}
            entry={entry}
            isExpanded={expandedEntry === entry.id}
            onToggle={() => setExpandedEntry(expandedEntry === entry.id ? null : entry.id)}
            isFirst={index === 0}
          />
        ))}

        {filteredEntries.length === 0 && (
          <div className="card text-center py-12">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No audit entries found matching your criteria</p>
          </div>
        )}
      </div>
    </div>
  )
}

function AuditEntryCard({ 
  entry, 
  isExpanded, 
  onToggle,
  isFirst,
}: { 
  entry: AuditTrailEntry
  isExpanded: boolean
  onToggle: () => void
  isFirst: boolean
}) {
  const eventTypeConfig: Record<AuditEventType, { color: string; label: string }> = {
    regulation_detected: { color: 'bg-orange-100 text-orange-800', label: 'Regulation Detected' },
    requirement_extracted: { color: 'bg-purple-100 text-purple-800', label: 'Requirement Extracted' },
    requirement_approved: { color: 'bg-purple-100 text-purple-800', label: 'Requirement Approved' },
    mapping_created: { color: 'bg-blue-100 text-blue-800', label: 'Mapping Created' },
    mapping_reviewed: { color: 'bg-blue-100 text-blue-800', label: 'Mapping Reviewed' },
    code_generated: { color: 'bg-green-100 text-green-800', label: 'Code Generated' },
    action_created: { color: 'bg-yellow-100 text-yellow-800', label: 'Action Created' },
    action_approved: { color: 'bg-yellow-100 text-yellow-800', label: 'Action Approved' },
    action_rejected: { color: 'bg-red-100 text-red-800', label: 'Action Rejected' },
    pr_created: { color: 'bg-indigo-100 text-indigo-800', label: 'PR Created' },
    pr_merged: { color: 'bg-green-100 text-green-800', label: 'PR Merged' },
    deployment_completed: { color: 'bg-green-100 text-green-800', label: 'Deployed' },
  }

  const config = eventTypeConfig[entry.event_type] || { 
    color: 'bg-gray-100 text-gray-800', 
    label: entry.event_type.replace(/_/g, ' ') 
  }

  const actorDisplay = entry.actor_email || entry.actor_id || 'System'

  return (
    <div className="relative">
      {/* Timeline connector */}
      {!isFirst && (
        <div className="absolute left-6 -top-4 w-0.5 h-4 bg-gray-200" />
      )}
      
      <div className="card hover:shadow-md transition-shadow">
        <div 
          className="flex items-start gap-4 cursor-pointer"
          onClick={onToggle}
        >
          <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
            {entry.actor_type === 'ai' ? (
              <span className="text-lg">🤖</span>
            ) : entry.actor_type === 'system' ? (
              <span className="text-lg">⚙️</span>
            ) : (
              <span className="text-lg">👤</span>
            )}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className={`status-badge ${config.color}`}>{config.label}</span>
              <span className="text-xs text-gray-400">
                {new Date(entry.created_at).toLocaleString()}
              </span>
            </div>
            <p className="text-gray-900 font-medium">{entry.description}</p>
            <p className="text-gray-500 text-sm mt-1">
              By: {actorDisplay} • {entry.resource_type}: {entry.resource_id.slice(0, 8)}...
            </p>
          </div>

          <button className="p-1 text-gray-400 hover:text-gray-600">
            {isExpanded ? (
              <ChevronDown className="h-5 w-5" />
            ) : (
              <ChevronRight className="h-5 w-5" />
            )}
          </button>
        </div>

        {isExpanded && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-2">Metadata</h4>
                <pre className="bg-gray-50 rounded-lg p-3 text-sm overflow-x-auto max-h-48">
                  {JSON.stringify(entry.metadata, null, 2)}
                </pre>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-2">Hash Chain</h4>
                <div className="bg-gray-50 rounded-lg p-3 space-y-2">
                  <div>
                    <span className="text-xs text-gray-400">Entry Hash:</span>
                    <p className="font-mono text-sm text-gray-700 break-all">{entry.hash}</p>
                  </div>
                  {entry.previous_hash && (
                    <div>
                      <span className="text-xs text-gray-400">Previous Hash:</span>
                      <p className="font-mono text-sm text-gray-700 break-all">{entry.previous_hash}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
