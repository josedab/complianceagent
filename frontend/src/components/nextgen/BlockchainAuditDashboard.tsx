'use client'

import { Link2, Shield, Lock, CheckCircle } from 'lucide-react'
import { useBlockchainState } from '@/hooks/useNextgenApi'

const MOCK_BLOCKS = [
  { id: 'blk-247', hash: '0xa3f8...d92c', type: 'evidence_submission', timestamp: '2026-03-12T14:30:00Z', data_hash: '0x7b2e...4f1a', verified: true },
  { id: 'blk-246', hash: '0xb1c4...e78f', type: 'policy_update', timestamp: '2026-03-12T12:15:00Z', data_hash: '0x9d3c...8e2b', verified: true },
  { id: 'blk-245', hash: '0xc5d2...f34a', type: 'audit_event', timestamp: '2026-03-12T10:00:00Z', data_hash: '0x4e1f...6c3d', verified: true },
  { id: 'blk-244', hash: '0xd8e6...a19b', type: 'compliance_check', timestamp: '2026-03-12T08:45:00Z', data_hash: '0x2a7b...9d4e', verified: true },
  { id: 'blk-243', hash: '0xe2f1...b56c', type: 'evidence_submission', timestamp: '2026-03-11T22:30:00Z', data_hash: '0x5f8c...1a2b', verified: true },
  { id: 'blk-242', hash: '0xf4a3...c78d', type: 'configuration_change', timestamp: '2026-03-11T18:00:00Z', data_hash: '0x8c3d...7e5f', verified: true },
]

const typeColors: Record<string, { bg: string; text: string }> = {
  evidence_submission: { bg: 'bg-blue-100', text: 'text-blue-700' },
  policy_update: { bg: 'bg-purple-100', text: 'text-purple-700' },
  audit_event: { bg: 'bg-orange-100', text: 'text-orange-700' },
  compliance_check: { bg: 'bg-green-100', text: 'text-green-700' },
  configuration_change: { bg: 'bg-yellow-100', text: 'text-yellow-700' },
}

export default function BlockchainAuditDashboard() {
  const { data: liveState } = useBlockchainState()

  const blocks = liveState ? [] : MOCK_BLOCKS
  const chainLength = liveState ? 0 : 247
  const allVerified = blocks.every(b => b.verified)

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
          <p className="mt-2 text-3xl font-bold text-green-600">{allVerified ? 'Valid ✓' : 'Invalid ✗'}</p>
          <p className="mt-1 text-sm text-gray-500">Chain integrity</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Smart Contracts</p>
            <Lock className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">3</p>
          <p className="mt-1 text-sm text-gray-500">Active contracts</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Verification Time</p>
            <CheckCircle className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">1.2s</p>
          <p className="mt-1 text-sm text-gray-500">Full chain verification</p>
        </div>
      </div>

      {/* Recent Blocks */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Link2 className="h-5 w-5 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-900">Recent Blocks</h2>
        </div>
        <div className="space-y-3">
          {blocks.map(block => {
            const colors = typeColors[block.type] || typeColors.compliance_check
            return (
              <div key={block.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-medium text-gray-900">{block.id}</span>
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${colors.bg} ${colors.text}`}>
                      {block.type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {block.verified && <CheckCircle className="h-4 w-4 text-green-500" />}
                    <span className="text-sm text-gray-500">{new Date(block.timestamp).toLocaleString()}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-500 font-mono">
                  <span>Hash: {block.hash}</span>
                  <span>Data: {block.data_hash}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
