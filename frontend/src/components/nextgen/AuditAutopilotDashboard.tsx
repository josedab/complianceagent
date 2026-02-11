'use client'

import { useState } from 'react'
import { ShieldCheck, FileSearch, Package, AlertCircle, CheckCircle, Clock, BarChart3, FileText } from 'lucide-react'
import { useGapAnalysis, useEvidencePackage, useReadinessReport } from '@/hooks/useNextgenApi'
import type { GapAnalysis, EvidencePackage, ReadinessReport, AuditFramework } from '@/types/nextgen'

const FRAMEWORKS: { id: AuditFramework; name: string; controls: number }[] = [
  { id: 'soc2', name: 'SOC 2 Type II', controls: 64 },
  { id: 'iso27001', name: 'ISO 27001', controls: 93 },
  { id: 'hipaa', name: 'HIPAA', controls: 54 },
  { id: 'pci_dss', name: 'PCI-DSS v4.0', controls: 78 },
]

const MOCK_GAP: Record<string, GapAnalysis> = {
  soc2: { id: 'g1', framework: 'soc2', total_controls: 64, controls_met: 48, controls_partial: 10, controls_missing: 6, readiness_score: 78.5, critical_gaps: ['CC6.1 - Logical access controls incomplete', 'CC7.2 - System monitoring gaps', 'CC8.1 - Change management process undocumented'], estimated_remediation_hours: 120 },
  iso27001: { id: 'g2', framework: 'iso27001', total_controls: 93, controls_met: 62, controls_partial: 18, controls_missing: 13, readiness_score: 71.2, critical_gaps: ['A.12.4 - Logging needs enhancement', 'A.14.2 - Secure development lifecycle', 'A.18.1 - Compliance with legal requirements'], estimated_remediation_hours: 200 },
  hipaa: { id: 'g3', framework: 'hipaa', total_controls: 54, controls_met: 38, controls_partial: 11, controls_missing: 5, readiness_score: 74.8, critical_gaps: ['164.312(a) - Access control audit logging', '164.312(e) - Transmission security gaps'], estimated_remediation_hours: 95 },
  pci_dss: { id: 'g4', framework: 'pci_dss', total_controls: 78, controls_met: 59, controls_partial: 12, controls_missing: 7, readiness_score: 80.1, critical_gaps: ['Req 3.4 - PAN rendering incomplete', 'Req 6.5 - Secure development training'], estimated_remediation_hours: 85 },
}

export default function AuditAutopilotDashboard() {
  const [selectedFramework, setSelectedFramework] = useState<AuditFramework>('soc2')
  const [gapResult, setGapResult] = useState<GapAnalysis | null>(null)
  const [evidenceResult, setEvidenceResult] = useState<EvidencePackage | null>(null)
  const [readinessResult, setReadinessResult] = useState<ReadinessReport | null>(null)

  const { mutate: runGap, loading: gapLoading } = useGapAnalysis()
  const { mutate: genEvidence, loading: evidenceLoading } = useEvidencePackage()
  const { mutate: genReadiness, loading: readinessLoading } = useReadinessReport()

  const handleGapAnalysis = async () => {
    try {
      const res = await runGap(selectedFramework)
      setGapResult(res)
    } catch {
      setGapResult(MOCK_GAP[selectedFramework] || MOCK_GAP.soc2)
    }
  }

  const handleEvidencePackage = async () => {
    try {
      const res = await genEvidence(selectedFramework)
      setEvidenceResult(res)
    } catch {
      setEvidenceResult({ id: 'ep1', framework: selectedFramework, title: `${selectedFramework.toUpperCase()} Evidence Package`, total_items: 42, controls_covered: 48, total_controls: 64, coverage_percent: 75.0 })
    }
  }

  const handleReadiness = async () => {
    try {
      const res = await genReadiness(selectedFramework)
      setReadinessResult(res)
    } catch {
      setReadinessResult({ id: 'rr1', framework: selectedFramework, overall_readiness: 78.5, recommendations: ['Complete access control audit logging for CC6.1', 'Implement continuous system monitoring per CC7.2', 'Document change management procedures for CC8.1', 'Schedule penetration test before audit window'], estimated_prep_weeks: 6.5 })
    }
  }

  const gap = gapResult || MOCK_GAP[selectedFramework]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Audit Preparation Autopilot</h1>
        <p className="text-gray-500">Automated gap analysis, evidence collection, and readiness reporting</p>
      </div>

      {/* Framework Selector */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {FRAMEWORKS.map((fw) => (
          <button
            key={fw.id}
            onClick={() => { setSelectedFramework(fw.id); setGapResult(null); setEvidenceResult(null); setReadinessResult(null); }}
            className={`card p-4 text-left transition-all ${selectedFramework === fw.id ? 'ring-2 ring-primary-500 border-primary-200' : 'hover:border-gray-300'}`}
          >
            <ShieldCheck className={`h-6 w-6 mb-2 ${selectedFramework === fw.id ? 'text-primary-600' : 'text-gray-400'}`} />
            <p className="font-semibold text-gray-900">{fw.name}</p>
            <p className="text-xs text-gray-500">{fw.controls} controls</p>
          </button>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button onClick={handleGapAnalysis} disabled={gapLoading} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2">
          {gapLoading ? <FileSearch className="h-4 w-4 animate-spin" /> : <FileSearch className="h-4 w-4" />}
          Run Gap Analysis
        </button>
        <button onClick={handleEvidencePackage} disabled={evidenceLoading} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
          {evidenceLoading ? <Package className="h-4 w-4 animate-spin" /> : <Package className="h-4 w-4" />}
          Generate Evidence Package
        </button>
        <button onClick={handleReadiness} disabled={readinessLoading} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2">
          {readinessLoading ? <BarChart3 className="h-4 w-4 animate-spin" /> : <BarChart3 className="h-4 w-4" />}
          Readiness Report
        </button>
      </div>

      {/* Gap Analysis Results */}
      {gap && (
        <div className="card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Gap Analysis: {selectedFramework.toUpperCase()}</h2>
            <div className="flex items-center gap-2">
              <span className={`text-2xl font-bold ${gap.readiness_score >= 80 ? 'text-green-600' : gap.readiness_score >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                {gap.readiness_score.toFixed(1)}%
              </span>
              <span className="text-sm text-gray-500">readiness</span>
            </div>
          </div>

          {/* Control Summary */}
          <div className="grid grid-cols-4 gap-3">
            <div className="p-3 bg-gray-50 rounded-lg text-center">
              <p className="text-xl font-bold text-gray-900">{gap.total_controls}</p>
              <p className="text-xs text-gray-500">Total Controls</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg text-center">
              <p className="text-xl font-bold text-green-700">{gap.controls_met}</p>
              <p className="text-xs text-green-600">Met</p>
            </div>
            <div className="p-3 bg-yellow-50 rounded-lg text-center">
              <p className="text-xl font-bold text-yellow-700">{gap.controls_partial}</p>
              <p className="text-xs text-yellow-600">Partial</p>
            </div>
            <div className="p-3 bg-red-50 rounded-lg text-center">
              <p className="text-xl font-bold text-red-700">{gap.controls_missing}</p>
              <p className="text-xs text-red-600">Missing</p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="h-4 bg-gray-200 rounded-full overflow-hidden flex">
            <div className="bg-green-500 h-full" style={{ width: `${(gap.controls_met / gap.total_controls) * 100}%` }} />
            <div className="bg-yellow-500 h-full" style={{ width: `${(gap.controls_partial / gap.total_controls) * 100}%` }} />
            <div className="bg-red-500 h-full" style={{ width: `${(gap.controls_missing / gap.total_controls) * 100}%` }} />
          </div>

          {/* Critical Gaps */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-1">
              <AlertCircle className="h-4 w-4 text-red-500" /> Critical Gaps
            </h3>
            <div className="space-y-2">
              {gap.critical_gaps.map((g, i) => (
                <div key={i} className="p-2 bg-red-50 rounded-lg flex items-center gap-2">
                  <span className="text-red-500">✗</span>
                  <span className="text-sm text-red-800">{g}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm text-gray-500 pt-2 border-t border-gray-100">
            <Clock className="h-4 w-4" />
            <span>Estimated remediation: {gap.estimated_remediation_hours} hours</span>
          </div>
        </div>
      )}

      {/* Evidence Package Result */}
      {evidenceResult && (
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Package className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Evidence Package</h2>
          </div>
          <div className="grid grid-cols-4 gap-3">
            <div className="p-3 bg-blue-50 rounded-lg text-center">
              <p className="text-xl font-bold text-blue-700">{evidenceResult.total_items}</p>
              <p className="text-xs text-blue-600">Evidence Items</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg text-center">
              <p className="text-xl font-bold text-green-700">{evidenceResult.controls_covered}</p>
              <p className="text-xs text-green-600">Controls Covered</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg text-center">
              <p className="text-xl font-bold text-gray-700">{evidenceResult.total_controls}</p>
              <p className="text-xs text-gray-500">Total Controls</p>
            </div>
            <div className="p-3 bg-primary-50 rounded-lg text-center">
              <p className="text-xl font-bold text-primary-700">{evidenceResult.coverage_percent.toFixed(1)}%</p>
              <p className="text-xs text-primary-600">Coverage</p>
            </div>
          </div>
        </div>
      )}

      {/* Readiness Report */}
      {readinessResult && (
        <div className="card p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-green-600" />
              <h2 className="text-lg font-semibold text-gray-900">Readiness Report</h2>
            </div>
            <span className={`text-xl font-bold ${readinessResult.overall_readiness >= 80 ? 'text-green-600' : 'text-yellow-600'}`}>
              {readinessResult.overall_readiness.toFixed(1)}% Ready
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
            <Clock className="h-4 w-4" />
            <span>Estimated prep time: {readinessResult.estimated_prep_weeks} weeks</span>
          </div>
          <div className="space-y-2">
            {readinessResult.recommendations.map((r, i) => (
              <div key={i} className="p-2 bg-gray-50 rounded-lg flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-primary-500 flex-shrink-0" />
                <span className="text-sm text-gray-700">{r}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
