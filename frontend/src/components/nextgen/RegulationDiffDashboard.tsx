'use client'

import { useState } from 'react'
import { FileText, GitCompare, AlertTriangle, Plus, Minus, Edit3, ChevronDown, ChevronUp } from 'lucide-react'

type ChangeSeverity = 'critical' | 'major' | 'minor' | 'clarification'
type ChangeType = 'addition' | 'deletion' | 'modification' | 'renumbering'


interface ArticleChange {
  article: string
  section: string
  changeType: ChangeType
  severity: ChangeSeverity
  oldText: string
  newText: string
  summary: string
  impactOnCode: string
  affectedControls: string[]
}

interface RegDiff {
  id: string
  regulation: string
  fromVersion: string
  toVersion: string
  totalChanges: number
  criticalChanges: number
  aiSummary: string
  impactAssessment: string
  changes: ArticleChange[]
}

const severityConfig: Record<ChangeSeverity, { label: string; color: string }> = {
  critical: { label: 'Critical', color: 'bg-red-100 text-red-700' },
  major: { label: 'Major', color: 'bg-orange-100 text-orange-700' },
  minor: { label: 'Minor', color: 'bg-yellow-100 text-yellow-700' },
  clarification: { label: 'Clarification', color: 'bg-blue-100 text-blue-700' },
}

const changeTypeConfig: Record<ChangeType, { icon: typeof Plus; color: string }> = {
  addition: { icon: Plus, color: 'text-green-600' },
  deletion: { icon: Minus, color: 'text-red-600' },
  modification: { icon: Edit3, color: 'text-blue-600' },
  renumbering: { icon: FileText, color: 'text-gray-600' },
}

const MOCK_DIFFS: RegDiff[] = [
  {
    id: 'gdpr-diff-1', regulation: 'GDPR', fromVersion: '2016/679', toVersion: '2024/1689-amend',
    totalChanges: 8, criticalChanges: 2,
    aiSummary: 'The AI Act introduces cross-references to GDPR for AI systems processing personal data. Key changes: new recital on AI training data, Art. 10a on data governance, and modified Art. 22 on automated decision-making.',
    impactAssessment: 'HIGH: Organizations using AI systems must cross-reference both GDPR and AI Act.',
    changes: [
      { article: 'Art. 22', section: 'Automated Decision-Making', changeType: 'modification', severity: 'critical',
        oldText: 'The data subject shall have the right not to be subject to a decision based solely on automated processing.',
        newText: 'The data subject shall have the right not to be subject to a decision based solely on automated processing, including profiling by AI systems as defined in Regulation (EU) 2024/1689.',
        summary: 'Expanded to explicitly include AI systems per EU AI Act.', impactOnCode: 'Update automated decision checks to include AI classification.',
        affectedControls: ['GDPR-Art22', 'AIACT-Art6'] },
      { article: 'Art. 10a', section: 'Data Governance for AI', changeType: 'addition', severity: 'critical',
        oldText: '', newText: 'Personal data used for training AI systems shall be subject to data governance measures ensuring data quality, relevance, and representativeness.',
        summary: 'New article requiring data governance for AI training data.', impactOnCode: 'Add data quality validation for ML training pipelines.',
        affectedControls: ['GDPR-Art10a', 'AIACT-Art10'] },
      { article: 'Recital 71', section: 'Profiling', changeType: 'modification', severity: 'major',
        oldText: 'The data subject should have the right not to be subject to profiling.',
        newText: 'The data subject should have the right not to be subject to profiling, which includes inference by AI systems.',
        summary: 'Clarified that AI inference constitutes profiling.', impactOnCode: 'Flag AI inference endpoints as profiling under GDPR.',
        affectedControls: [] },
    ],
  },
  {
    id: 'pci-diff-1', regulation: 'PCI-DSS', fromVersion: '3.2.1', toVersion: '4.0.1',
    totalChanges: 64, criticalChanges: 12,
    aiSummary: 'PCI-DSS v4.0.1 introduces major changes: customized approach, MFA everywhere, targeted risk analysis, and new e-commerce requirements.',
    impactAssessment: 'CRITICAL: All organizations must migrate by March 31, 2025.',
    changes: [
      { article: 'Req. 8.3.6', section: 'Multi-Factor Authentication', changeType: 'modification', severity: 'critical',
        oldText: 'MFA for remote access to CDE.', newText: 'MFA for ALL access to the CDE, not just remote access.',
        summary: 'MFA now required for all CDE access.', impactOnCode: 'Implement MFA on all CDE-accessing endpoints.',
        affectedControls: ['PCI-8.3.6'] },
      { article: 'Req. 6.4.3', section: 'Payment Page Scripts', changeType: 'addition', severity: 'critical',
        oldText: '', newText: 'All payment page scripts must be managed with a method to confirm script integrity.',
        summary: 'New SRI requirement for payment pages.', impactOnCode: 'Add Subresource Integrity to all payment page scripts.',
        affectedControls: ['PCI-6.4.3'] },
    ],
  },
]

export default function RegulationDiffDashboard() {
  const [selectedDiff, setSelectedDiff] = useState<string | null>(null)
  const [expandedChange, setExpandedChange] = useState<string | null>(null)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><GitCompare className="h-7 w-7 text-cyan-600" /> Regulation Diff Viewer</h1>
        <p className="text-gray-500 mt-1">Visual diffs between regulation versions with AI-powered change summaries</p>
      </div>

      {/* Diff List */}
      <div className="space-y-4">
        {MOCK_DIFFS.map(diff => (
          <div key={diff.id} className="bg-white rounded-lg border overflow-hidden">
            <div className="p-5 cursor-pointer hover:bg-gray-50" onClick={() => setSelectedDiff(selectedDiff === diff.id ? null : diff.id)}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded font-medium">{diff.regulation}</span>
                    <span className="text-sm text-gray-500">{diff.fromVersion} → {diff.toVersion}</span>
                    {diff.criticalChanges > 0 && (
                      <span className="bg-red-100 text-red-700 text-xs px-2 py-0.5 rounded flex items-center gap-1">
                        <AlertTriangle className="h-3 w-3" />{diff.criticalChanges} critical
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 mt-2">{diff.aiSummary}</p>
                  <div className="mt-2 text-sm"><span className="font-medium">Impact: </span><span className="text-red-600">{diff.impactAssessment}</span></div>
                  <div className="text-xs text-gray-500 mt-1">{diff.totalChanges} total changes</div>
                </div>
                {selectedDiff === diff.id ? <ChevronUp className="h-5 w-5 text-gray-400" /> : <ChevronDown className="h-5 w-5 text-gray-400" />}
              </div>
            </div>

            {selectedDiff === diff.id && (
              <div className="border-t divide-y">
                {diff.changes.map((change, idx) => {
                  const sev = severityConfig[change.severity]
                  const ct = changeTypeConfig[change.changeType]
                  const ChangeIcon = ct.icon
                  const key = `${diff.id}-${idx}`
                  const expanded = expandedChange === key

                  return (
                    <div key={idx} className="p-4 cursor-pointer hover:bg-gray-50" onClick={() => setExpandedChange(expanded ? null : key)}>
                      <div className="flex items-center gap-2">
                        <ChangeIcon className={`h-4 w-4 ${ct.color}`} />
                        <span className="font-medium">{change.article}</span>
                        <span className="text-sm text-gray-500">— {change.section}</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${sev.color}`}>{sev.label}</span>
                      </div>
                      <p className="text-sm text-gray-700 mt-1">{change.summary}</p>

                      {expanded && (
                        <div className="mt-3 space-y-3">
                          {change.oldText && (
                            <div className="bg-red-50 rounded p-3 border-l-4 border-red-300">
                              <div className="text-xs text-red-600 font-medium mb-1">- Removed</div>
                              <p className="text-sm text-red-800">{change.oldText}</p>
                            </div>
                          )}
                          {change.newText && (
                            <div className="bg-green-50 rounded p-3 border-l-4 border-green-300">
                              <div className="text-xs text-green-600 font-medium mb-1">+ Added</div>
                              <p className="text-sm text-green-800">{change.newText}</p>
                            </div>
                          )}
                          {change.impactOnCode && (
                            <div className="bg-blue-50 rounded p-3">
                              <div className="text-xs text-blue-600 font-medium mb-1">💻 Code Impact</div>
                              <p className="text-sm text-blue-800">{change.impactOnCode}</p>
                            </div>
                          )}
                          {change.affectedControls.length > 0 && (
                            <div className="flex gap-1">
                              {change.affectedControls.map(c => (
                                <span key={c} className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded">{c}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
