'use client'

import { useState } from 'react'
import { Vote, ThumbsUp, ThumbsDown, Minus, Users, FileText, Clock, Shield, Hash } from 'lucide-react'

type ProposalStatus = 'draft' | 'active' | 'passed' | 'rejected' | 'executed' | 'expired'
type ProposalType = 'policy_change' | 'framework_addition' | 'threshold_update' | 'member_admission' | 'budget_allocation' | 'emergency_action'

interface Proposal {
  id: string
  title: string
  description: string
  proposalType: ProposalType
  status: ProposalStatus
  proposerOrg: string
  affectedFrameworks: string[]
  changesSummary: string
  votesFor: number
  votesAgainst: number
  votesAbstain: number
  totalVoters: number
  quorumRequired: number
  approvalThreshold: number
  votingPeriodHours: number
  votingEndsAt: string | null
  executionHash: string
}

const statusConfig: Record<ProposalStatus, { label: string; color: string }> = {
  draft: { label: 'Draft', color: 'bg-gray-100 text-gray-800' },
  active: { label: 'Active', color: 'bg-blue-100 text-blue-800' },
  passed: { label: 'Passed', color: 'bg-green-100 text-green-800' },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-800' },
  executed: { label: 'Executed', color: 'bg-purple-100 text-purple-800' },
  expired: { label: 'Expired', color: 'bg-yellow-100 text-yellow-800' },
}

const typeConfig: Record<ProposalType, { label: string; icon: string }> = {
  policy_change: { label: 'Policy Change', icon: '📝' },
  framework_addition: { label: 'Framework Addition', icon: '🆕' },
  threshold_update: { label: 'Threshold Update', icon: '📊' },
  member_admission: { label: 'Member Admission', icon: '👤' },
  budget_allocation: { label: 'Budget Allocation', icon: '💰' },
  emergency_action: { label: 'Emergency Action', icon: '🚨' },
}

const MOCK_PROPOSALS: Proposal[] = [
  {
    id: '1', title: 'Add EU AI Act Framework Support',
    description: 'Proposal to add comprehensive EU AI Act compliance framework including risk classification, transparency requirements, and conformity assessment procedures.',
    proposalType: 'framework_addition', status: 'active', proposerOrg: 'Acme Corp',
    affectedFrameworks: ['EU AI Act', 'GDPR'], changesSummary: 'Add 47 new controls for AI system compliance across risk categories.',
    votesFor: 3.5, votesAgainst: 0.5, votesAbstain: 0.3, totalVoters: 3,
    quorumRequired: 0.6, approvalThreshold: 0.66, votingPeriodHours: 48,
    votingEndsAt: new Date(Date.now() + 36 * 3600000).toISOString(), executionHash: '',
  },
  {
    id: '2', title: 'Increase PCI-DSS Violation Threshold',
    description: 'Raise the minimum confidence threshold for PCI-DSS violation detection from 70% to 85% to reduce false positives.',
    proposalType: 'threshold_update', status: 'passed', proposerOrg: 'FinanceHQ',
    affectedFrameworks: ['PCI-DSS'], changesSummary: 'Update confidence threshold from 0.70 to 0.85.',
    votesFor: 4.8, votesAgainst: 0.5, votesAbstain: 0, totalVoters: 4,
    quorumRequired: 0.6, approvalThreshold: 0.66, votingPeriodHours: 48,
    votingEndsAt: null, executionHash: 'a1b2c3d4e5f67890',
  },
  {
    id: '3', title: 'Emergency: Disable Flawed HIPAA Rule',
    description: 'Emergency proposal to disable HIPAA-PHI-017 rule that generates false positives on anonymized research data.',
    proposalType: 'emergency_action', status: 'active', proposerOrg: 'TechStartup Inc',
    affectedFrameworks: ['HIPAA'], changesSummary: 'Temporarily disable HIPAA-PHI-017 pending investigation.',
    votesFor: 1.5, votesAgainst: 2.0, votesAbstain: 0, totalVoters: 2,
    quorumRequired: 0.6, approvalThreshold: 0.66, votingPeriodHours: 24,
    votingEndsAt: new Date(Date.now() + 12 * 3600000).toISOString(), executionHash: '',
  },
]

const MOCK_STATS = {
  totalProposals: 3, activeProposals: 2, passedProposals: 1, rejectedProposals: 0,
  totalMembers: 3, totalVotesCast: 9, avgParticipation: 0.78, avgApproval: 0.33,
}

export default function DAOGovernanceDashboard() {
  const [selectedProposal, setSelectedProposal] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const filtered = statusFilter === 'all' ? MOCK_PROPOSALS : MOCK_PROPOSALS.filter(p => p.status === statusFilter)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Vote className="h-7 w-7 text-purple-600" /> Compliance DAO Governance</h1>
          <p className="text-gray-500 mt-1">Decentralized governance for compliance policy decisions</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Proposals', value: MOCK_STATS.totalProposals, icon: FileText },
          { label: 'Active Votes', value: MOCK_STATS.activeProposals, icon: Clock },
          { label: 'Members', value: MOCK_STATS.totalMembers, icon: Users },
          { label: 'Participation', value: `${(MOCK_STATS.avgParticipation * 100).toFixed(0)}%`, icon: Shield },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-lg border p-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm"><stat.icon className="h-4 w-4" />{stat.label}</div>
            <div className="text-2xl font-bold mt-1">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {['all', 'active', 'passed', 'rejected'].map(s => (
          <button key={s} onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 rounded-full text-sm ${statusFilter === s ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Proposals */}
      <div className="space-y-4">
        {filtered.map(proposal => {
          const total = proposal.votesFor + proposal.votesAgainst + proposal.votesAbstain
          const forPct = total > 0 ? (proposal.votesFor / total) * 100 : 0
          const againstPct = total > 0 ? (proposal.votesAgainst / total) * 100 : 0
          const type = typeConfig[proposal.proposalType]
          const status = statusConfig[proposal.status]

          return (
            <div key={proposal.id} className="bg-white rounded-lg border p-5 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => setSelectedProposal(selectedProposal === proposal.id ? null : proposal.id)}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span>{type.icon}</span>
                    <span className="text-xs text-gray-500">{type.label}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${status.color}`}>{status.label}</span>
                  </div>
                  <h3 className="text-lg font-semibold">{proposal.title}</h3>
                  <p className="text-gray-600 text-sm mt-1">{proposal.description}</p>
                  <div className="flex gap-2 mt-2">
                    {proposal.affectedFrameworks.map(fw => (
                      <span key={fw} className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded">{fw}</span>
                    ))}
                    <span className="text-xs text-gray-400">by {proposal.proposerOrg}</span>
                  </div>
                </div>
              </div>

              {/* Vote Bar */}
              <div className="mt-4">
                <div className="flex justify-between text-sm mb-1">
                  <span className="flex items-center gap-1 text-green-600"><ThumbsUp className="h-3 w-3" /> {proposal.votesFor.toFixed(1)}</span>
                  <span className="flex items-center gap-1 text-red-600"><ThumbsDown className="h-3 w-3" /> {proposal.votesAgainst.toFixed(1)}</span>
                  <span className="flex items-center gap-1 text-gray-400"><Minus className="h-3 w-3" /> {proposal.votesAbstain.toFixed(1)}</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full flex overflow-hidden">
                  <div className="bg-green-500 h-full" style={{ width: `${forPct}%` }} />
                  <div className="bg-red-500 h-full" style={{ width: `${againstPct}%` }} />
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>{proposal.totalVoters} voters</span>
                  <span>Threshold: {(proposal.approvalThreshold * 100).toFixed(0)}%</span>
                  {proposal.votingEndsAt && <span>Ends: {new Date(proposal.votingEndsAt).toLocaleDateString()}</span>}
                </div>
              </div>

              {/* Expanded Details */}
              {selectedProposal === proposal.id && (
                <div className="mt-4 pt-4 border-t space-y-3">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Changes Summary</h4>
                    <p className="text-sm text-gray-600">{proposal.changesSummary}</p>
                  </div>
                  {proposal.executionHash && (
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Hash className="h-4 w-4" /> Execution Hash: <code className="bg-gray-50 px-2 py-0.5 rounded text-xs">{proposal.executionHash}</code>
                    </div>
                  )}
                  {proposal.status === 'active' && (
                    <div className="flex gap-2">
                      <button className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">Vote For</button>
                      <button className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700">Vote Against</button>
                      <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300">Abstain</button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
