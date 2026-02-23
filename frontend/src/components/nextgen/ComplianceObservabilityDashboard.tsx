'use client'

import { useState } from 'react'
import { Activity, BarChart3, Bell, Monitor } from 'lucide-react'

interface ObservabilityMetric {
  id: string
  name: string
  source: string
  value: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  alertCount: number
  status: 'healthy' | 'degraded' | 'critical' | 'unknown'
}

const statusColors: Record<ObservabilityMetric['status'], string> = {
  healthy: 'text-green-700 bg-green-100',
  degraded: 'text-yellow-700 bg-yellow-100',
  critical: 'text-red-700 bg-red-100',
  unknown: 'text-gray-700 bg-gray-100',
}

const trendIcons: Record<ObservabilityMetric['trend'], string> = {
  up: '↑',
  down: '↓',
  stable: '→',
}

const MOCK_METRICS: ObservabilityMetric[] = [
  { id: 'm1', name: 'Policy Evaluation Latency', source: 'OPA Gateway', value: 12.4, unit: 'ms', trend: 'down', alertCount: 0, status: 'healthy' },
  { id: 'm2', name: 'Compliance Check Throughput', source: 'Audit Pipeline', value: 8420, unit: 'req/min', trend: 'up', alertCount: 2, status: 'degraded' },
  { id: 'm3', name: 'Evidence Collection Rate', source: 'Evidence Collector', value: 99.2, unit: '%', trend: 'stable', alertCount: 0, status: 'healthy' },
  { id: 'm4', name: 'Alert Response Time', source: 'Incident Manager', value: 340, unit: 'sec', trend: 'up', alertCount: 5, status: 'critical' },
]

export default function ComplianceObservabilityDashboard() {
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  const filtered = selectedStatus === 'all'
    ? MOCK_METRICS
    : MOCK_METRICS.filter(m => m.status === selectedStatus)

  const healthyCount = MOCK_METRICS.filter(m => m.status === 'healthy').length
  const totalAlerts = MOCK_METRICS.reduce((a, m) => a + m.alertCount, 0)
  const criticalCount = MOCK_METRICS.filter(m => m.status === 'critical').length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Activity className="h-6 w-6 text-indigo-600" />
          Compliance Observability Pipeline
        </h1>
        <p className="text-gray-500">Real-time monitoring of compliance infrastructure health</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Active Metrics</p>
            <Monitor className="h-5 w-5 text-indigo-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-indigo-600">{MOCK_METRICS.length}</p>
          <p className="mt-1 text-sm text-gray-500">{healthyCount} healthy</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Throughput</p>
            <BarChart3 className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">8.4K</p>
          <p className="mt-1 text-sm text-gray-500">req/min peak</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Active Alerts</p>
            <Bell className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{totalAlerts}</p>
          <p className="mt-1 text-sm text-gray-500">{criticalCount} critical</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Uptime</p>
            <Activity className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">99.9%</p>
          <p className="mt-1 text-sm text-gray-500">Last 30 days</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {['all', 'healthy', 'degraded', 'critical'].map(s => (
          <button
            key={s}
            onClick={() => setSelectedStatus(s)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium ${
              selectedStatus === s ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {filtered.map(metric => (
          <div key={metric.id} className="card">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${statusColors[metric.status]}`}>
                    {metric.status.charAt(0).toUpperCase() + metric.status.slice(1)}
                  </span>
                  <span className="text-xs text-gray-500">{metric.source}</span>
                  {metric.alertCount > 0 && (
                    <span className="px-2 py-0.5 text-xs rounded-full font-medium text-red-700 bg-red-100">
                      {metric.alertCount} alerts
                    </span>
                  )}
                </div>
                <h3 className="font-semibold text-gray-900">{metric.name}</h3>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {metric.value}{metric.unit === '%' ? '%' : ''}
                </p>
                <p className="text-xs text-gray-500">
                  {trendIcons[metric.trend]} {metric.unit !== '%' ? metric.unit : 'uptime'}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
