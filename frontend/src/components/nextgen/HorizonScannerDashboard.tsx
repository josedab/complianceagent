'use client'

import { AlertTriangle, Calendar, Globe, Eye } from 'lucide-react'

const MOCK_LEGISLATION = [
  { id: '1', title: 'EU AI Act - Full Enforcement', jurisdiction: 'EU', status: 'enacted', confidence: 'high', frameworks: ['EU AI Act', 'GDPR'], months_ahead: 3, tags: ['ai', 'transparency'] },
  { id: '2', title: 'Digital Operational Resilience Act (DORA)', jurisdiction: 'EU', status: 'effective', confidence: 'high', frameworks: ['DORA', 'NIS2'], months_ahead: 0, tags: ['financial', 'ict-risk'] },
  { id: '3', title: 'American Privacy Rights Act (APRA)', jurisdiction: 'US', status: 'committee', confidence: 'low', frameworks: ['CCPA', 'GDPR'], months_ahead: 18, tags: ['privacy', 'federal'] },
  { id: '4', title: 'PCI-DSS v4.0.1 Enforcement Deadline', jurisdiction: 'Global', status: 'enacted', confidence: 'high', frameworks: ['PCI-DSS'], months_ahead: 2, tags: ['payment', 'security'] },
  { id: '5', title: 'SEC Climate Disclosure Rules - Phase 2', jurisdiction: 'US', status: 'passed', confidence: 'high', frameworks: ['SEC Climate', 'TCFD'], months_ahead: 6, tags: ['esg', 'climate'] },
  { id: '6', title: 'UK AI Safety Bill', jurisdiction: 'UK', status: 'proposed', confidence: 'medium', frameworks: ['EU AI Act'], months_ahead: 12, tags: ['ai', 'safety'] },
  { id: '7', title: 'India DPDP Rules', jurisdiction: 'India', status: 'draft', confidence: 'medium', frameworks: ['India DPDP'], months_ahead: 4, tags: ['privacy', 'apac'] },
]

const urgencyColor = (months: number) => {
  if (months <= 3) return { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' }
  if (months <= 6) return { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' }
  if (months <= 12) return { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' }
  return { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' }
}

const statusBadge = (status: string) => {
  const map: Record<string, string> = {
    effective: 'bg-green-100 text-green-700',
    enacted: 'bg-blue-100 text-blue-700',
    passed: 'bg-indigo-100 text-indigo-700',
    committee: 'bg-yellow-100 text-yellow-700',
    proposed: 'bg-orange-100 text-orange-700',
    draft: 'bg-gray-100 text-gray-600',
  }
  return map[status] || 'bg-gray-100 text-gray-600'
}

export default function HorizonScannerDashboard() {
  const imminent = MOCK_LEGISLATION.filter(l => l.months_ahead <= 3)
  const upcoming = MOCK_LEGISLATION.filter(l => l.months_ahead > 3 && l.months_ahead <= 12)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Horizon Scanner</h1>
        <p className="text-gray-500">Track upcoming legislation and predict codebase impact</p>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Tracked</p>
            <Eye className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{MOCK_LEGISLATION.length}</p>
          <p className="mt-1 text-sm text-gray-500">regulations monitored</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Imminent</p>
            <AlertTriangle className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{imminent.length}</p>
          <p className="mt-1 text-sm text-gray-500">within 3 months</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Upcoming</p>
            <Calendar className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{upcoming.length}</p>
          <p className="mt-1 text-sm text-gray-500">3-12 months</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Jurisdictions</p>
            <Globe className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{new Set(MOCK_LEGISLATION.map(l => l.jurisdiction)).size}</p>
          <p className="mt-1 text-sm text-gray-500">regions covered</p>
        </div>
      </div>

      {/* Timeline */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Regulatory Timeline</h2>
        <div className="space-y-3">
          {MOCK_LEGISLATION.sort((a, b) => a.months_ahead - b.months_ahead).map(leg => {
            const colors = urgencyColor(leg.months_ahead)
            return (
              <div key={leg.id} className={`p-4 rounded-lg border ${colors.border} ${colors.bg}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className={`font-medium ${colors.text}`}>{leg.title}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${statusBadge(leg.status)}`}>
                        {leg.status}
                      </span>
                    </div>
                    <div className="mt-1 flex items-center gap-3 text-sm text-gray-500">
                      <span>{leg.jurisdiction}</span>
                      <span>•</span>
                      <span>{leg.frameworks.join(', ')}</span>
                    </div>
                    <div className="mt-2 flex gap-1.5">
                      {leg.tags.map(tag => (
                        <span key={tag} className="text-xs bg-white/60 px-2 py-0.5 rounded text-gray-600">{tag}</span>
                      ))}
                    </div>
                  </div>
                  <div className="text-right ml-4">
                    <p className={`text-lg font-bold ${colors.text}`}>
                      {leg.months_ahead === 0 ? 'Now' : `${leg.months_ahead}mo`}
                    </p>
                    <p className="text-xs text-gray-400">
                      {leg.confidence} confidence
                    </p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
