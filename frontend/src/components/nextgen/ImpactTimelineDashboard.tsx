'use client'

import { useState } from 'react'
import { Calendar, Clock, AlertTriangle, CheckCircle, ChevronRight, ListTodo, Globe, Filter } from 'lucide-react'
import { useImpactTimeline, useRemediationTasks, useGenerateTimelineTasks } from '@/hooks/useNextgenApi'
import type { TimelineView, TimelineEvent, RemediationTask } from '@/types/nextgen'

const MOCK_TIMELINE: TimelineView = {
  events: [
    { id: 'e1', title: 'EU AI Act - High-Risk AI Systems', event_type: 'regulation_effective', framework: 'EU AI Act', jurisdiction: 'EU', days_remaining: 45, impact_score: 9.2, estimated_effort_hours: 160, affected_repos: ['ai-platform', 'ml-service'], is_predicted: false, confidence: 1.0 },
    { id: 'e2', title: 'DORA - ICT Risk Management', event_type: 'enforcement_deadline', framework: 'DORA', jurisdiction: 'EU', days_remaining: 90, impact_score: 8.5, estimated_effort_hours: 120, affected_repos: ['banking-api', 'payment-gateway'], is_predicted: false, confidence: 1.0 },
    { id: 'e3', title: 'NIS2 Directive - Security Requirements', event_type: 'regulation_effective', framework: 'NIS2', jurisdiction: 'EU', days_remaining: 120, impact_score: 7.8, estimated_effort_hours: 80, affected_repos: ['infrastructure', 'security-service'], is_predicted: false, confidence: 1.0 },
    { id: 'e4', title: 'GDPR - Updated Cookie Guidelines', event_type: 'guidance_update', framework: 'GDPR', jurisdiction: 'EU', days_remaining: 180, impact_score: 5.5, estimated_effort_hours: 40, affected_repos: ['web-frontend', 'consent-service'], is_predicted: false, confidence: 0.95 },
    { id: 'e5', title: 'India DPDP Act - Cross-Border Rules', event_type: 'predicted', framework: 'DPDP', jurisdiction: 'India', days_remaining: 270, impact_score: 6.8, estimated_effort_hours: 60, affected_repos: ['data-service'], is_predicted: true, confidence: 0.72 },
    { id: 'e6', title: 'SEC Climate Disclosure - Phase 2', event_type: 'enforcement_deadline', framework: 'SEC Climate', jurisdiction: 'US', days_remaining: 365, impact_score: 4.2, estimated_effort_hours: 30, affected_repos: ['reporting-service'], is_predicted: true, confidence: 0.65 },
  ],
  total_events: 6,
  upcoming_deadlines: 4,
  overdue_count: 0,
  total_effort_hours: 490,
}

const MOCK_TASKS: RemediationTask[] = [
  { id: 't1', title: 'Implement AI system risk classification', priority: 'critical', status: 'pending', estimated_hours: 40, due_date: '2026-03-30' },
  { id: 't2', title: 'Build transparency documentation generator', priority: 'high', status: 'in_progress', estimated_hours: 24, due_date: '2026-03-15' },
  { id: 't3', title: 'Add human oversight mechanisms', priority: 'high', status: 'pending', estimated_hours: 32, due_date: '2026-04-01' },
  { id: 't4', title: 'Update ICT risk management framework', priority: 'medium', status: 'pending', estimated_hours: 20, due_date: '2026-05-15' },
]

const urgencyColor = (days: number) => {
  if (days <= 30) return 'bg-red-100 text-red-700 border-red-200'
  if (days <= 90) return 'bg-orange-100 text-orange-700 border-orange-200'
  if (days <= 180) return 'bg-yellow-100 text-yellow-700 border-yellow-200'
  return 'bg-green-100 text-green-700 border-green-200'
}

const priorityColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-green-100 text-green-700',
}

const statusColors: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-700',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  blocked: 'bg-red-100 text-red-700',
}

export default function ImpactTimelineDashboard() {
  const [framework, setFramework] = useState<string>('')
  const { data: liveTimeline } = useImpactTimeline(framework || undefined)
  const { data: liveTasks } = useRemediationTasks()
  const { mutate: generateTasks, loading: generating } = useGenerateTimelineTasks()

  const timeline = liveTimeline || MOCK_TIMELINE
  const tasks = liveTasks || MOCK_TASKS

  const handleGenerateTasks = async (eventId: string) => {
    try { await generateTasks(eventId) } catch { /* demo mode */ }
  }

  const frameworks = Array.from(new Set(timeline.events.map(e => e.framework)))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Regulatory Impact Timeline</h1>
          <p className="text-gray-500">Track upcoming regulatory changes and auto-generate remediation tasks</p>
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <select
            value={framework}
            onChange={(e) => setFramework(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:border-primary-500 focus:outline-none"
          >
            <option value="">All Frameworks</option>
            {frameworks.map(fw => <option key={fw} value={fw}>{fw}</option>)}
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Calendar className="h-5 w-5 text-blue-600" />} title="Total Events" value={timeline.total_events.toString()} subtitle="Regulatory changes tracked" />
        <StatCard icon={<Clock className="h-5 w-5 text-orange-600" />} title="Upcoming Deadlines" value={timeline.upcoming_deadlines.toString()} subtitle="Within next 12 months" />
        <StatCard icon={<AlertTriangle className="h-5 w-5 text-red-600" />} title="Overdue" value={timeline.overdue_count.toString()} subtitle="Past deadline" />
        <StatCard icon={<ListTodo className="h-5 w-5 text-purple-600" />} title="Total Effort" value={`${timeline.total_effort_hours}h`} subtitle="Estimated remediation" />
      </div>

      {/* Timeline */}
      <div className="card p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Regulatory Events</h2>
        <div className="space-y-3">
          {timeline.events.map((event) => (
            <TimelineEventCard key={event.id} event={event} onGenerateTasks={handleGenerateTasks} generating={generating} />
          ))}
        </div>
      </div>

      {/* Remediation Tasks */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-4">
          <ListTodo className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Remediation Tasks</h2>
        </div>
        <div className="space-y-2">
          {tasks.map((task) => (
            <div key={task.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100 hover:border-primary-200 transition-colors">
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${priorityColors[task.priority] || 'bg-gray-100 text-gray-700'}`}>
                  {task.priority}
                </span>
                <span className="text-sm font-medium text-gray-900">{task.title}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 text-xs rounded-full ${statusColors[task.status] || 'bg-gray-100 text-gray-700'}`}>
                  {task.status.replace('_', ' ')}
                </span>
                <span className="text-xs text-gray-500">{task.estimated_hours}h</span>
                {task.due_date && <span className="text-xs text-gray-400">{task.due_date}</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function TimelineEventCard({ event, onGenerateTasks, generating }: { event: TimelineEvent; onGenerateTasks: (id: string) => void; generating: boolean }) {
  return (
    <div className={`p-4 rounded-lg border ${urgencyColor(event.days_remaining)}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {event.is_predicted && <span className="px-1.5 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">Predicted</span>}
            <span className="px-1.5 py-0.5 text-xs bg-white/50 rounded">{event.event_type.replace('_', ' ')}</span>
            <Globe className="h-3 w-3 text-gray-400" />
            <span className="text-xs text-gray-500">{event.jurisdiction}</span>
          </div>
          <h3 className="font-semibold text-gray-900">{event.title}</h3>
          <p className="text-sm text-gray-600 mt-1">{event.framework}</p>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {event.days_remaining} days remaining</span>
            <span>Impact: {event.impact_score.toFixed(1)}/10</span>
            <span>Effort: {event.estimated_effort_hours}h</span>
            {event.is_predicted && <span>Confidence: {(event.confidence * 100).toFixed(0)}%</span>}
          </div>
          {event.affected_repos.length > 0 && (
            <div className="flex gap-1 mt-2">
              {event.affected_repos.map(r => <span key={r} className="px-2 py-0.5 bg-white/60 text-gray-600 text-xs rounded">{r}</span>)}
            </div>
          )}
        </div>
        <button
          onClick={() => onGenerateTasks(event.id)}
          disabled={generating}
          className="flex items-center gap-1 px-3 py-1.5 text-xs bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <CheckCircle className="h-3 w-3" /> Generate Tasks <ChevronRight className="h-3 w-3" />
        </button>
      </div>
    </div>
  )
}

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-2"><p className="text-sm font-medium text-gray-500">{title}</p>{icon}</div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
    </div>
  )
}
