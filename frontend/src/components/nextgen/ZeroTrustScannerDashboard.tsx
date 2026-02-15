'use client'

import { Shield, Lock, AlertTriangle, CheckCircle } from 'lucide-react'
import { useZeroTrustViolations } from '@/hooks/useNextgenApi'
import type { ZeroTrustViolation } from '@/types/nextgen'

interface ZeroTrustViolationDisplay extends ZeroTrustViolation {
  resource: string;
  violation: string;
  remediation: string;
}

const MOCK_VIOLATIONS: ZeroTrustViolationDisplay[] = [
  { id: 'zt1', policy_id: 'pol1', resource_name: 'api-gateway', violation_type: 'no_mtls', severity: 'critical', description: 'No mTLS enforcement on internal APIs', framework: 'NIST ZTA', remediation_hint: 'Enable mutual TLS on all service-to-service communication', iac_file: '', status: 'open', detected_at: '2026-03-12T10:00:00Z', resource: 'api-gateway', violation: 'No mTLS enforcement on internal APIs', remediation: 'Enable mutual TLS on all service-to-service communication' },
  { id: 'zt2', policy_id: 'pol2', resource_name: 'user-service', violation_type: 'excessive_permissions', severity: 'high', description: 'Service account with excessive permissions', framework: 'BeyondCorp', remediation_hint: 'Apply least-privilege IAM policy', iac_file: '', status: 'open', detected_at: '2026-03-11T14:00:00Z', resource: 'user-service', violation: 'Service account with excessive permissions', remediation: 'Apply least-privilege IAM policy' },
  { id: 'zt3', policy_id: 'pol3', resource_name: 'data-pipeline', violation_type: 'unencrypted_data', severity: 'medium', description: 'Unencrypted data at rest in staging', framework: 'NIST ZTA', remediation_hint: 'Enable AES-256 encryption for all data stores', iac_file: '', status: 'open', detected_at: '2026-03-10T09:00:00Z', resource: 'data-pipeline', violation: 'Unencrypted data at rest in staging', remediation: 'Enable AES-256 encryption for all data stores' },
  { id: 'zt4', policy_id: 'pol4', resource_name: 'k8s-cluster', violation_type: 'privileged_containers', severity: 'high', description: 'Pod security policy allows privileged containers', framework: 'CIS Benchmark', remediation_hint: 'Restrict pod security to baseline profile', iac_file: '', status: 'open', detected_at: '2026-03-12T08:30:00Z', resource: 'k8s-cluster', violation: 'Pod security policy allows privileged containers', remediation: 'Restrict pod security to baseline profile' },
  { id: 'zt5', policy_id: 'pol5', resource_name: 'cdn-config', violation_type: 'missing_headers', severity: 'low', description: 'Missing CSP headers on static assets', framework: 'BeyondCorp', remediation_hint: 'Add Content-Security-Policy headers', iac_file: '', status: 'open', detected_at: '2026-03-09T16:00:00Z', resource: 'cdn-config', violation: 'Missing CSP headers on static assets', remediation: 'Add Content-Security-Policy headers' },
]

const severityColors: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  low: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
}

export default function ZeroTrustScannerDashboard() {
  const { data: liveViolations } = useZeroTrustViolations()

  const violations = (liveViolations as ZeroTrustViolationDisplay[] | null) || MOCK_VIOLATIONS
  const criticalHigh = violations.filter(v => v.severity === 'critical' || v.severity === 'high').length
  const complianceScore = ((1 - violations.length / 156) * 100).toFixed(1)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Zero-Trust Compliance Architecture Scanner</h1>
        <p className="text-gray-500">Scan infrastructure-as-code for zero-trust compliance violations</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Resources Scanned</p>
            <Shield className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">156</p>
          <p className="mt-1 text-sm text-gray-500">Infrastructure resources</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Violations</p>
            <AlertTriangle className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{violations.length}</p>
          <p className="mt-1 text-sm text-red-500">{criticalHigh} critical/high</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Compliance Score</p>
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{complianceScore}%</p>
          <p className="mt-1 text-sm text-gray-500">Zero-trust posture</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Policies Active</p>
            <Lock className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">12</p>
          <p className="mt-1 text-sm text-gray-500">Enforcement policies</p>
        </div>
      </div>

      {/* Violations List */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          <h2 className="text-lg font-semibold text-gray-900">Violations</h2>
        </div>
        <div className="space-y-3">
          {violations.map(v => {
            const colors = severityColors[v.severity] || severityColors.medium
            return (
              <div key={v.id} className={`p-4 rounded-lg border ${colors.border} ${colors.bg}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${colors.text} bg-white`}>{v.severity}</span>
                    <span className="px-2 py-0.5 bg-white text-gray-600 text-xs rounded-full">{v.framework}</span>
                  </div>
                  <span className="text-sm text-gray-500">{v.resource}</span>
                </div>
                <p className={`font-medium ${colors.text}`}>{v.violation}</p>
                <p className="mt-1 text-sm text-gray-600">💡 {v.remediation}</p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
