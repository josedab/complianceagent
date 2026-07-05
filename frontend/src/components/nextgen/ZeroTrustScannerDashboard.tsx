'use client'

import { Shield, Lock, AlertTriangle, CheckCircle } from 'lucide-react'
import { useZeroTrustViolations } from '@/hooks/useNextgenApi'
import type { ZeroTrustViolation } from '@/types/nextgen'

const severityColors: Record<string, { bg: string; text: string; border: string }> = {
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  low: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
}

export default function ZeroTrustScannerDashboard() {
  const { data: liveViolations, loading, error, refetch } = useZeroTrustViolations()

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
        <p className="text-red-800">Error loading Zero-Trust Scanner: {error.message}</p>
        <button onClick={refetch} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const violations: ZeroTrustViolation[] = liveViolations ?? []
  const criticalHigh = violations.filter(v => v.severity === 'critical' || v.severity === 'high').length
  const complianceScore = violations.length > 0 ? ((1 - violations.length / 156) * 100).toFixed(1) : '100.0'

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
        {violations.length === 0 ? (
          <p className="text-gray-500 text-sm">No violations detected.</p>
        ) : (
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
                    <span className="text-sm text-gray-500">{v.resource_name}</span>
                  </div>
                  <p className={`font-medium ${colors.text}`}>{v.description}</p>
                  <p className="mt-1 text-sm text-gray-600">💡 {v.remediation_hint}</p>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
