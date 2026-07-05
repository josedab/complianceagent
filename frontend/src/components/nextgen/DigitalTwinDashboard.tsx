'use client'

import { useState } from 'react'
import { Layers, Activity, GitCompare, AlertTriangle, Clock } from 'lucide-react'
import { useTwinEvents, usePostureTimeline } from '@/hooks/useNextgenApi'

export default function DigitalTwinDashboard() {
  const [activeTab, setActiveTab] = useState<'snapshots' | 'simulations'>('snapshots')

  const { data: twinEvents, loading: eventsLoading, error: eventsError, refetch: refetchEvents } = useTwinEvents()
  const { data: postureTimeline, loading: timelineLoading, error: timelineError, refetch: refetchTimeline } = usePostureTimeline(30)

  const loading = eventsLoading || timelineLoading
  const error = eventsError || timelineError

  const refetch = () => { refetchEvents(); refetchTimeline() }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
        </div>
        <div className="card h-48 animate-pulse bg-gray-100" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading Compliance Digital Twin: {error.message}</p>
        <button onClick={refetch} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const events = twinEvents ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Compliance Digital Twin</h1>
        <p className="text-gray-500 mt-1">Real-time virtual replica of your compliance posture with what-if simulation</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><Layers className="w-4 h-4" /> Events</div>
          <div className="text-2xl font-bold">{events.length}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><Activity className="w-4 h-4" /> Timeline Days</div>
          <div className="text-2xl font-bold">{postureTimeline ? String(postureTimeline['days'] ?? 30) : '30'}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><AlertTriangle className="w-4 h-4" /> Snapshots</div>
          <div className="text-2xl font-bold">{postureTimeline ? String(postureTimeline['snapshot_count'] ?? '—') : '—'}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><GitCompare className="w-4 h-4" /> Changes</div>
          <div className="text-2xl font-bold">{postureTimeline ? String(postureTimeline['change_count'] ?? '—') : '—'}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b">
        <button onClick={() => setActiveTab('snapshots')} className={`pb-2 px-1 text-sm font-medium ${activeTab === 'snapshots' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}>
          <Layers className="w-4 h-4 inline mr-1" /> Live Events
        </button>
        <button onClick={() => setActiveTab('simulations')} className={`pb-2 px-1 text-sm font-medium ${activeTab === 'simulations' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}>
          <GitCompare className="w-4 h-4 inline mr-1" /> Posture Timeline
        </button>
      </div>

      {/* Content */}
      {activeTab === 'snapshots' && (
        events.length === 0 ? (
          <div className="card text-center py-8 text-gray-500">No twin events yet.</div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg border">
            <table className="w-full">
              <thead>
                <tr className="border-b text-left text-sm text-gray-500">
                  <th className="p-3">Repository</th>
                  <th className="p-3">Score</th>
                  <th className="p-3">Issues</th>
                  <th className="p-3">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event, i) => {
                  const repo = String(event['repository'] ?? event['repo'] ?? '—')
                  const score = event['overall_score'] != null ? Number(event['overall_score']) : null
                  const issues = event['issues_count'] != null ? Number(event['issues_count']) : null
                  const ts = String(event['timestamp'] ?? event['created_at'] ?? '')
                  return (
                    <tr key={String(event['id'] ?? i)} className="border-b last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="p-3 font-medium">{repo}</td>
                      <td className="p-3">
                        {score != null ? (
                          <span className={`font-bold ${score >= 85 ? 'text-green-600' : score >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>{score}%</span>
                        ) : '—'}
                      </td>
                      <td className="p-3">{issues != null ? issues : '—'}</td>
                      <td className="p-3 text-sm text-gray-500">{ts ? <><Clock className="w-3 h-3 inline mr-1" />{new Date(ts).toLocaleString()}</> : '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )
      )}

      {activeTab === 'simulations' && (
        postureTimeline == null ? (
          <div className="card text-center py-8 text-gray-500">No posture timeline data available.</div>
        ) : (
          <div className="space-y-3">
            {Object.entries(postureTimeline).map(([key, value]) => (
              <div key={key} className="bg-white dark:bg-gray-800 rounded-lg border p-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-gray-700 capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className="text-gray-900 font-mono text-sm">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                </div>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
