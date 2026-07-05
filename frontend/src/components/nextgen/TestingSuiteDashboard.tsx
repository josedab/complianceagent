'use client'

import { useState } from 'react'
import { Shield, CheckCircle, Clock, Zap, Code2 } from 'lucide-react'
import { useTestPatterns, useGenerateTestSuite } from '@/hooks/useNextgenApi'
import type {
  TestSuiteResult,
  ComplianceTestPattern,
  TestFramework,
} from '@/types/nextgen'

export default function TestingSuiteDashboard() {
  const [selectedRegulation, setSelectedRegulation] = useState('all')
  const [selectedFramework, setSelectedFramework] = useState<TestFramework>('pytest')
  const [suite, setSuite] = useState<TestSuiteResult | null>(null)

  const { data: livePatterns, loading: patternsLoading, error: patternsError, refetch: refetchPatterns } = useTestPatterns(
    selectedRegulation === 'all' ? undefined : selectedRegulation
  )
  const { mutate: generateSuite, loading: generating } = useGenerateTestSuite()

  if (patternsLoading) {
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

  if (patternsError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading Testing Suite: {patternsError.message}</p>
        <button onClick={refetchPatterns} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const patterns = livePatterns ?? []
  const filteredPatterns = selectedRegulation === 'all'
    ? patterns
    : patterns.filter(p => p.regulation === selectedRegulation)

  const regulations = ['all', ...Array.from(new Set(patterns.map(p => p.regulation)))]

  const handleGenerate = async () => {
    const result = await generateSuite({
      regulation: selectedRegulation === 'all' ? 'GDPR' : selectedRegulation,
      framework: selectedFramework,
    })
    setSuite(result)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Compliance Testing Suite</h1>
        <p className="text-gray-500">Generate and manage compliance test suites for your codebase</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Shield className="h-5 w-5 text-blue-600" />} title="Test Patterns" value={patterns.length.toString()} subtitle="Available templates" />
        <StatCard icon={<Code2 className="h-5 w-5 text-purple-600" />} title="Generated Tests" value={suite ? suite.total_tests.toString() : '—'} subtitle={suite ? `${suite.framework} framework` : 'Run generation first'} />
        <StatCard icon={<Zap className="h-5 w-5 text-green-600" />} title="Coverage" value={suite ? `${suite.coverage_estimate.toFixed(1)}%` : '—'} subtitle="Estimated compliance coverage" />
        <StatCard icon={<Clock className="h-5 w-5 text-orange-600" />} title="Generation Time" value={suite ? `${suite.generation_time_ms.toFixed(0)}ms` : '—'} subtitle="Last suite generation" />
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
        {filteredPatterns.length === 0 ? (
          <p className="text-gray-500 text-sm">No test patterns available yet.</p>
        ) : (
          <div className="space-y-3">
            {filteredPatterns.map((pattern: ComplianceTestPattern) => (
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
        )}
      </div>

      {/* Generated Tests */}
      {suite && suite.status === 'completed' && (
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
