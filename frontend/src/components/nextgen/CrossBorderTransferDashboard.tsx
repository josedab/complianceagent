'use client'

import { Globe, Shield, AlertTriangle, FileText } from 'lucide-react'
import { useDataFlows } from '@/hooks/useNextgenApi'
import type { DataFlowRecord } from '@/types/nextgen'

const MOCK_FLOWS: DataFlowRecord[] = [
  { id: 'df1', source_jurisdiction: 'EU-Frankfurt', destination_jurisdiction: 'US-East', transfer_mechanism: 'SCC', risk_level: 'medium', is_compliant: true, data_categories: ['personal', 'financial'], data_subjects: [], purpose: 'Data processing', volume_estimate: '12.4 GB', services_involved: [], detected_at: '2026-03-10T08:00:00Z' },
  { id: 'df2', source_jurisdiction: 'EU-Dublin', destination_jurisdiction: 'UK-London', transfer_mechanism: 'Adequacy', risk_level: 'low', is_compliant: true, data_categories: ['personal'], data_subjects: [], purpose: 'Data sync', volume_estimate: '8.1 GB', services_involved: [], detected_at: '2026-03-11T14:30:00Z' },
  { id: 'df3', source_jurisdiction: 'EU-Paris', destination_jurisdiction: 'CN-Beijing', transfer_mechanism: 'BCR', risk_level: 'high', is_compliant: false, data_categories: ['personal', 'health'], data_subjects: [], purpose: 'Analytics', volume_estimate: '3.2 GB', services_involved: [], detected_at: '2026-03-09T11:00:00Z' },
  { id: 'df4', source_jurisdiction: 'EU-Berlin', destination_jurisdiction: 'IN-Mumbai', transfer_mechanism: 'SCC', risk_level: 'high', is_compliant: false, data_categories: ['financial'], data_subjects: [], purpose: 'Processing', volume_estimate: '5.7 GB', services_involved: [], detected_at: '2026-03-12T06:45:00Z' },
]

const riskColors: Record<string, { bg: string; text: string }> = {
  low: { bg: 'bg-green-50', text: 'text-green-700' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700' },
  high: { bg: 'bg-red-50', text: 'text-red-700' },
}

export default function CrossBorderTransferDashboard() {
  const { data: liveFlows } = useDataFlows()

  const flows = liveFlows || MOCK_FLOWS
  const compliant = flows.filter(f => f.is_compliant).length
  const nonCompliant = flows.filter(f => !f.is_compliant).length
  const activeSCCs = flows.filter(f => f.transfer_mechanism === 'SCC').length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cross-Border Data Transfer Automation</h1>
        <p className="text-gray-500">Monitor and automate GDPR-compliant cross-border data transfers</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Total Flows</p>
            <Globe className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{flows.length}</p>
          <p className="mt-1 text-sm text-gray-500">Active data transfers</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Compliant</p>
            <Shield className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{compliant}</p>
          <p className="mt-1 text-sm text-gray-500">Passing all checks</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Non-Compliant</p>
            <AlertTriangle className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{nonCompliant}</p>
          <p className="mt-1 text-sm text-gray-500">Require remediation</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Active SCCs</p>
            <FileText className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">{activeSCCs}</p>
          <p className="mt-1 text-sm text-gray-500">Standard Contractual Clauses</p>
        </div>
      </div>

      {/* Data Flows Table */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="h-5 w-5 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-900">Data Flows</h2>
        </div>
        <div className="space-y-3">
          {flows.map(flow => {
            const colors = riskColors[flow.risk_level] || riskColors.medium
            return (
              <div key={flow.id} className={`p-4 rounded-lg border ${flow.is_compliant ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{flow.source_jurisdiction}</span>
                    <span className="text-gray-400">→</span>
                    <span className="font-medium text-gray-900">{flow.destination_jurisdiction}</span>
                  </div>
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${flow.is_compliant ? 'text-green-700 bg-white' : 'text-red-700 bg-white'}`}>
                    {flow.is_compliant ? 'compliant' : 'non compliant'}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>Mechanism: {flow.transfer_mechanism}</span>
                  <span className={`px-2 py-0.5 text-xs rounded-full ${colors.bg} ${colors.text}`}>{flow.risk_level} risk</span>
                  <span>{flow.volume_estimate}</span>
                  <span>{flow.detected_at ? new Date(flow.detected_at).toLocaleDateString() : 'N/A'}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
