'use client'

import { FileText, AlertTriangle, Download } from 'lucide-react'

const MOCK_SUMMARY = {
  overall_score: 85.5,
  overall_status: 'green',
  period: 'Q1 2026',
  highlights: [
    { category: 'GDPR', score: 87.0, status: 'green', trend: 'improving' },
    { category: 'SOC 2', score: 92.0, status: 'green', trend: 'stable' },
    { category: 'HIPAA', score: 78.0, status: 'yellow', trend: 'declining' },
    { category: 'PCI-DSS', score: 85.0, status: 'green', trend: 'improving' },
  ],
  top_risks: [
    { risk: 'HIPAA PHI encryption gap in legacy module', severity: 'high', eta: '2 weeks' },
    { risk: 'GDPR consent banner missing on mobile', severity: 'medium', eta: '1 week' },
    { risk: 'SOC 2 access review overdue for 3 users', severity: 'low', eta: '3 days' },
  ],
  action_items: [
    'Prioritize HIPAA remediation — score at 78%',
    'Complete Q1 access review before audit deadline',
    'Schedule EU AI Act readiness assessment',
  ],
}

const statusColors: Record<string, string> = {
  green: 'text-green-600',
  yellow: 'text-yellow-600',
  red: 'text-red-600',
}

const trendIcons: Record<string, string> = {
  improving: '↑',
  stable: '→',
  declining: '↓',
}

const severityBadge: Record<string, string> = {
  high: 'bg-red-100 text-red-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-green-100 text-green-700',
}

export default function BoardReportsDashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Board Compliance Report</h1>
          <p className="text-gray-500">{MOCK_SUMMARY.period} — Executive Summary</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Download className="h-4 w-4" />
          Export PDF
        </button>
      </div>

      {/* Overall score */}
      <div className="card text-center py-8">
        <p className="text-sm font-medium text-gray-500">Overall Compliance Score</p>
        <p className={`text-6xl font-bold mt-2 ${statusColors[MOCK_SUMMARY.overall_status]}`}>
          {MOCK_SUMMARY.overall_score}%
        </p>
        <p className="mt-2 text-gray-500">Across {MOCK_SUMMARY.highlights.length} frameworks</p>
      </div>

      {/* Framework scores */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {MOCK_SUMMARY.highlights.map(h => (
          <div key={h.category} className="card">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-gray-500">{h.category}</p>
              <span className="text-sm">{trendIcons[h.trend]}</span>
            </div>
            <p className={`mt-2 text-3xl font-bold ${statusColors[h.status]}`}>{h.score}%</p>
            <p className="mt-1 text-sm text-gray-400 capitalize">{h.trend}</p>
          </div>
        ))}
      </div>

      {/* Risks */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          <h2 className="text-lg font-semibold text-gray-900">Top Risks</h2>
        </div>
        <div className="space-y-3">
          {MOCK_SUMMARY.top_risks.map((risk, i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2 py-0.5 rounded-full ${severityBadge[risk.severity]}`}>
                  {risk.severity}
                </span>
                <span className="text-sm text-gray-700">{risk.risk}</span>
              </div>
              <span className="text-sm text-gray-400">ETA: {risk.eta}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Action items */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <FileText className="h-5 w-5 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-900">Action Items</h2>
        </div>
        <ol className="space-y-2">
          {MOCK_SUMMARY.action_items.map((item, i) => (
            <li key={i} className="flex items-start gap-3 p-2">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-xs font-bold">{i + 1}</span>
              <span className="text-sm text-gray-700">{item}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
