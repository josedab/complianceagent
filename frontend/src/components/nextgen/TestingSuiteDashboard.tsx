'use client'

import { useState } from 'react'
import { Shield, CheckCircle, Clock, Zap, Code2 } from 'lucide-react'
import { useTestPatterns, useGenerateTestSuite } from '@/hooks/useNextgenApi'
import type {
  TestSuiteResult,
  ComplianceTestPattern,
  TestFramework,
} from '@/types/nextgen'

const MOCK_PATTERNS: ComplianceTestPattern[] = [
  { id: 'gdpr-consent-001', name: 'GDPR Consent Collection', category: 'consent', regulation: 'GDPR', description: 'Verify consent before processing', assertions: ['consent_exists', 'purpose_specified'], tags: ['gdpr', 'art-6'] },
  { id: 'gdpr-deletion-002', name: 'GDPR Right to Erasure', category: 'data_deletion', regulation: 'GDPR', description: 'Verify complete data deletion', assertions: ['data_deleted', 'audit_preserved'], tags: ['gdpr', 'art-17'] },
  { id: 'hipaa-encryption-001', name: 'HIPAA PHI Encryption', category: 'encryption', regulation: 'HIPAA', description: 'Verify PHI encrypted at rest', assertions: ['data_encrypted', 'approved_algorithm'], tags: ['hipaa', 'security-rule'] },
  { id: 'pci-tokenization-001', name: 'PCI Card Tokenization', category: 'tokenization', regulation: 'PCI-DSS', description: 'Verify card data tokenization', assertions: ['pan_not_stored', 'no_plaintext_in_logs'], tags: ['pci-dss', 'req-3'] },
  { id: 'ai-act-transparency-001', name: 'EU AI Act Transparency', category: 'ai_transparency', regulation: 'EU_AI_ACT', description: 'Verify AI transparency info', assertions: ['risk_level_classified', 'purpose_documented'], tags: ['eu-ai-act', 'art-13'] },
]

const MOCK_SUITE: TestSuiteResult = {
  id: 'suite-001',
  status: 'completed',
  regulation: 'GDPR',
  framework: 'pytest',
  tests: [
    { id: 't1', pattern_id: 'gdpr-consent-001', test_name: 'test_consent_collection', test_code: '# consent test...', framework: 'pytest', regulation: 'GDPR', requirement_ref: 'Art. 6, Art. 7', description: 'Verify consent before data processing', confidence: 0.92, target_file: 'src/consent.py' },
    { id: 't2', pattern_id: 'gdpr-deletion-002', test_name: 'test_right_to_erasure', test_code: '# erasure test...', framework: 'pytest', regulation: 'GDPR', requirement_ref: 'Art. 17', description: 'Verify complete data deletion on request', confidence: 0.88, target_file: 'src/users.py' },
    { id: 't3', pattern_id: 'gdpr-access-003', test_name: 'test_dsar_export', test_code: '# DSAR test...', framework: 'pytest', regulation: 'GDPR', requirement_ref: 'Art. 15', description: 'Verify DSAR exports complete data', confidence: 0.85, target_file: 'src/api/dsar.py' },
  ],
  patterns_used: ['gdpr-consent-001', 'gdpr-deletion-002', 'gdpr-access-003'],
  total_tests: 3,
  coverage_estimate: 25.5,
  generation_time_ms: 342,
}

export default function TestingSuiteDashboard() {
  const [selectedRegulation, setSelectedRegulation] = useState('all')
  const [selectedFramework, setSelectedFramework] = useState<TestFramework>('pytest')
  const [suite, setSuite] = useState<TestSuiteResult>(MOCK_SUITE)

  const { data: livePatterns } = useTestPatterns(
    selectedRegulation === 'all' ? undefined : selectedRegulation
  )
  const { mutate: generateSuite, loading: generating } = useGenerateTestSuite()

  const patterns = livePatterns || MOCK_PATTERNS
  const filteredPatterns = selectedRegulation === 'all'
    ? patterns
    : patterns.filter(p => p.regulation === selectedRegulation)

  const regulations = ['all', ...Array.from(new Set(patterns.map(p => p.regulation)))]

  const handleGenerate = async () => {
    try {
      const result = await generateSuite({
        regulation: selectedRegulation === 'all' ? 'GDPR' : selectedRegulation,
        framework: selectedFramework,
      })
      setSuite(result)
    } catch {
      // Keep mock data on error
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Compliance Testing Suite</h1>
        <p className="text-gray-500">Generate and manage compliance test suites for your codebase</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Shield className="h-5 w-5 text-blue-600" />} title="Test Patterns" value={MOCK_PATTERNS.length.toString()} subtitle="Available templates" />
        <StatCard icon={<Code2 className="h-5 w-5 text-purple-600" />} title="Generated Tests" value={suite.total_tests.toString()} subtitle={`${suite.framework} framework`} />
        <StatCard icon={<Zap className="h-5 w-5 text-green-600" />} title="Coverage" value={`${suite.coverage_estimate.toFixed(1)}%`} subtitle="Estimated compliance coverage" />
        <StatCard icon={<Clock className="h-5 w-5 text-orange-600" />} title="Generation Time" value={`${suite.generation_time_ms.toFixed(0)}ms`} subtitle="Last suite generation" />
      </div>

      {/* Controls */}
      <div className="card">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Regulation</label>
            <select value={selectedRegulation} onChange={e => setSelectedRegulation(e.target.value)} className="rounded-md border border-gray-300 px-3 py-2 text-sm">
              {regulations.map(r => <option key={r} value={r}>{r === 'all' ? 'All Regulations' : r}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Framework</label>
            <select value={selectedFramework} onChange={e => setSelectedFramework(e.target.value as TestFramework)} className="rounded-md border border-gray-300 px-3 py-2 text-sm">
              <option value="pytest">Pytest</option>
              <option value="jest">Jest</option>
              <option value="junit">JUnit</option>
            </select>
          </div>
          <div className="ml-auto mt-5">
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
            >
              {generating ? 'Generating...' : 'Generate Test Suite'}
            </button>
          </div>
        </div>
      </div>

      {/* Patterns */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Test Patterns ({filteredPatterns.length})</h2>
        <div className="space-y-3">
          {filteredPatterns.map(pattern => (
            <div key={pattern.id} className="flex items-start gap-3 p-3 rounded-lg border border-gray-100 hover:border-primary-200 transition-colors">
              <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{pattern.name}</span>
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">{pattern.regulation}</span>
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">{pattern.category}</span>
                </div>
                <p className="text-sm text-gray-500 mt-1">{pattern.description}</p>
                <div className="flex gap-1 mt-2">
                  {pattern.assertions.map(a => (
                    <span key={a} className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded">{a}</span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Generated Tests */}
      {suite.status === 'completed' && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Generated Tests</h2>
          <div className="space-y-3">
            {suite.tests.map(test => (
              <div key={test.id} className="p-3 rounded-lg border border-gray-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Code2 className="h-4 w-4 text-purple-500" />
                    <span className="font-mono text-sm text-gray-900">{test.test_name}</span>
                  </div>
                  <span className={`px-2 py-0.5 text-xs rounded-full ${test.confidence >= 0.9 ? 'bg-green-100 text-green-700' : test.confidence >= 0.8 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                    {(test.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">{test.description}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                  <span>📁 {test.target_file}</span>
                  <span>📋 {test.requirement_ref}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        {icon}
      </div>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
    </div>
  )
}
