'use client'

import { Link2, Shield, Lock, CheckCircle } from 'lucide-react'
import { useBlockchainState, useBlockchainVerification } from '@/hooks/useNextgenApi'

export default function BlockchainAuditDashboard() {
  const { data: state, loading: stateLoading, error: stateError, refetch: refetchState } = useBlockchainState()
  const { data: verification, loading: verifyLoading, error: verifyError, refetch: refetchVerify } = useBlockchainVerification()

  const loading = stateLoading || verifyLoading
  const error = stateError || verifyError

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
        </div>
        <div className="card h-64 animate-pulse bg-gray-100" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading Blockchain Audit Trail: {error.message}</p>
        <button onClick={() => { refetchState(); refetchVerify(); }} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const chainLength = state?.chain_length ?? 0
  const isValid = state?.is_valid ?? false
  const invalidBlockCount = verification?.invalid_blocks?.length ?? 0
  const verificationTimeMs = verification?.verification_time_ms != null
    ? `${(verification.verification_time_ms / 1000).toFixed(1)}s`
    : '—'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Blockchain-Based Compliance Audit Trail</h1>
        <p className="text-gray-500">Immutable, cryptographically verified audit trail</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Chain Length</p>
            <Link2 className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{chainLength}</p>
          <p className="mt-1 text-sm text-gray-500">Total blocks</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Status</p>
            <Shield className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{isValid ? 'Valid ✓' : 'Invalid ✗'}</p>
          <p className="mt-1 text-sm text-gray-500">Chain integrity</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Invalid Blocks</p>
            <Lock className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">{invalidBlockCount}</p>
          <p className="mt-1 text-sm text-gray-500">Integrity violations</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Verification Time</p>
            <CheckCircle className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{verificationTimeMs}</p>
          <p className="mt-1 text-sm text-gray-500">Full chain verification</p>
        </div>
      </div>

      {/* Chain Summary */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Link2 className="h-5 w-5 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-900">Chain Summary</h2>
        </div>
        {state ? (
          <div className="space-y-3">
            <div className="p-4 rounded-lg border border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900">Latest Block Hash</span>
                <CheckCircle className={`h-4 w-4 ${state.is_valid ? 'text-green-500' : 'text-red-500'}`} />
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-500 font-mono">
                <span>{state.latest_hash}</span>
              </div>
            </div>
            <p className="text-xs text-gray-400 px-1">
              Individual block records are available via the audit API. Chain integrity is confirmed via cryptographic verification above.
            </p>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No blockchain state data available.</p>
        )}
      </div>
    </div>
  )
}
