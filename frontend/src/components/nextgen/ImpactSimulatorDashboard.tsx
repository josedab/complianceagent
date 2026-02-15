'use client'

import { useState } from 'react'
import { Target, AlertTriangle, Clock, Layers, TrendingUp } from 'lucide-react'
import type { BlastRadiusAnalysis, BlastRadiusComponent } from '@/types/nextgen'

const MOCK_ANALYSIS: BlastRadiusAnalysis = {
  scenario_id: 'sim-001',
  total_components: 8,
  critical_count: 2,
  high_count: 2,
  medium_count: 2,
  low_count: 2,
  components: [
    { component_path: 'src/auth/', component_type: 'module', impact_level: 'critical', regulations_affected: ['GDPR'], estimated_effort_hours: 16, change_type: 'modification', description: 'Authentication module needs consent flow update' },
    { component_path: 'src/data/storage.py', component_type: 'file', impact_level: 'critical', regulations_affected: ['GDPR'], estimated_effort_hours: 12, change_type: 'modification', description: 'Data storage retention policy update required' },
    { component_path: 'src/api/endpoints/', component_type: 'module', impact_level: 'high', regulations_affected: ['GDPR', 'CCPA'], estimated_effort_hours: 8, change_type: 'modification', description: 'API endpoints need privacy headers' },
    { component_path: 'src/models/user.py', component_type: 'file', impact_level: 'high', regulations_affected: ['GDPR'], estimated_effort_hours: 6, change_type: 'addition', description: 'User model needs PII field annotations' },
    { component_path: 'src/services/encryption.py', component_type: 'file', impact_level: 'medium', regulations_affected: ['PCI-DSS'], estimated_effort_hours: 4, change_type: 'review_only', description: 'Encryption service review for algorithm compliance' },
    { component_path: 'src/middleware/consent.py', component_type: 'file', impact_level: 'medium', regulations_affected: ['GDPR'], estimated_effort_hours: 4, change_type: 'addition', description: 'New consent management middleware' },
    { component_path: 'src/logging/audit.py', component_type: 'file', impact_level: 'low', regulations_affected: ['SOC2'], estimated_effort_hours: 2, change_type: 'modification', description: 'Audit log format update' },
    { component_path: 'infrastructure/terraform/', component_type: 'module', impact_level: 'low', regulations_affected: ['SOC2'], estimated_effort_hours: 2, change_type: 'review_only', description: 'Infrastructure config review' },
  ],
  total_effort_hours: 54,
  risk_score: 7.2,
}

const impactColors: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  low: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
}

export default function ImpactSimulatorDashboard() {
  const [analysis] = useState<BlastRadiusAnalysis>(MOCK_ANALYSIS)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulatory Impact Simulator</h1>
        <p className="text-gray-500">What-if analysis with blast radius visualization and scenario comparison</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Total Components</p>
            <Layers className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{analysis.total_components}</p>
          <p className="mt-1 text-sm text-gray-500">Affected by change</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Critical Impact</p>
            <AlertTriangle className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{analysis.critical_count}</p>
          <p className="mt-1 text-sm text-gray-500">{analysis.high_count} high impact</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Effort Estimate</p>
            <Clock className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">{analysis.total_effort_hours}h</p>
          <p className="mt-1 text-sm text-gray-500">{Math.round(analysis.total_effort_hours / 8)} dev-days</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Risk Score</p>
            <TrendingUp className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{analysis.risk_score}/10</p>
          <p className="mt-1 text-sm text-gray-500">Overall risk</p>
        </div>
      </div>

      {/* Blast Radius */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Target className="h-5 w-5 text-red-500" />
          <h2 className="text-lg font-semibold text-gray-900">Blast Radius Analysis</h2>
        </div>
        <div className="space-y-3">
          {analysis.components.map((comp: BlastRadiusComponent, i: number) => {
            const colors = impactColors[comp.impact_level] || impactColors.medium
            return (
              <div key={i} className={`p-4 rounded-lg border ${colors.border} ${colors.bg}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${colors.text} bg-white`}>{comp.impact_level}</span>
                    <span className="font-mono text-sm text-gray-800">{comp.component_path}</span>
                    <span className="px-2 py-0.5 bg-white text-gray-600 text-xs rounded-full">{comp.component_type}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-600">{comp.estimated_effort_hours}h effort</span>
                </div>
                <p className={`text-sm ${colors.text}`}>{comp.description}</p>
                <div className="flex items-center gap-2 mt-2">
                  {comp.regulations_affected.map(reg => (
                    <span key={reg} className="px-2 py-0.5 bg-white text-gray-600 text-xs rounded-full border">{reg}</span>
                  ))}
                  <span className="px-2 py-0.5 bg-white text-gray-500 text-xs rounded-full border">{comp.change_type.replace('_', ' ')}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
