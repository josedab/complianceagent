'use client'

import { TestTube2, CheckSquare, BarChart3, AlertCircle } from 'lucide-react'
import { useRegulationCoverages } from '@/hooks/useNextgenApi'
import type { RegulationCoverageRecord } from '@/types/nextgen'

interface CoverageDisplay extends RegulationCoverageRecord {
  id: string;
  total_requirements: number;
  covered: number;
  test_suites: number;
  last_generated: string;
}

const MOCK_COVERAGES: CoverageDisplay[] = [
  { id: 'rc1', regulation: 'GDPR', total_articles: 42, covered_articles: 35, coverage_pct: 83.3, uncovered_articles: [], status: 'active', total_requirements: 42, covered: 35, test_suites: 2, last_generated: '2026-03-10T10:00:00Z' },
  { id: 'rc2', regulation: 'SOC 2', total_articles: 38, covered_articles: 28, coverage_pct: 73.7, uncovered_articles: [], status: 'active', total_requirements: 38, covered: 28, test_suites: 1, last_generated: '2026-03-09T14:00:00Z' },
  { id: 'rc3', regulation: 'HIPAA', total_articles: 25, covered_articles: 15, coverage_pct: 60.0, uncovered_articles: [], status: 'active', total_requirements: 25, covered: 15, test_suites: 1, last_generated: '2026-03-08T09:00:00Z' },
  { id: 'rc4', regulation: 'PCI DSS', total_articles: 30, covered_articles: 22, coverage_pct: 73.3, uncovered_articles: [], status: 'active', total_requirements: 30, covered: 22, test_suites: 1, last_generated: '2026-03-07T16:00:00Z' },
  { id: 'rc5', regulation: 'ISO 27001', total_articles: 35, covered_articles: 27, coverage_pct: 77.1, uncovered_articles: [], status: 'active', total_requirements: 35, covered: 27, test_suites: 0, last_generated: '2026-03-06T11:00:00Z' },
]

export default function RegulationTestGenDashboard() {
  const { data: liveCoverages } = useRegulationCoverages()

  const coverages = (liveCoverages as CoverageDisplay[] | null) || MOCK_COVERAGES
  const totalSuites = coverages.reduce((sum, c) => sum + c.test_suites, 0)
  const totalTests = coverages.reduce((sum, c) => sum + c.covered, 0)
  const avgCoverage = (coverages.reduce((sum, c) => sum + c.coverage_pct, 0) / coverages.length).toFixed(1)
  const uncovered = coverages.filter(c => c.coverage_pct < 70).length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Regulation-to-Test-Case Generator</h1>
        <p className="text-gray-500">Auto-generate compliance test suites from regulatory requirements</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Test Suites</p>
            <TestTube2 className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{totalSuites}</p>
          <p className="mt-1 text-sm text-gray-500">Generated suites</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Total Tests</p>
            <CheckSquare className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{totalTests}</p>
          <p className="mt-1 text-sm text-gray-500">Across all regulations</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Avg Coverage</p>
            <BarChart3 className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">{avgCoverage}%</p>
          <p className="mt-1 text-sm text-gray-500">Requirement coverage</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Uncovered Regs</p>
            <AlertCircle className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{uncovered}</p>
          <p className="mt-1 text-sm text-red-500">Below 70% threshold</p>
        </div>
      </div>

      {/* Coverage Bars */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-5 w-5 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-900">Regulation Coverage</h2>
        </div>
        <div className="space-y-4">
          {coverages.map(cov => (
            <div key={cov.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900">{cov.regulation}</span>
                <span className={`text-sm font-bold ${cov.coverage_pct >= 70 ? 'text-green-600' : 'text-red-600'}`}>{cov.coverage_pct.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                <div
                  className={`h-2.5 rounded-full ${cov.coverage_pct >= 80 ? 'bg-green-500' : cov.coverage_pct >= 70 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${cov.coverage_pct}%` }}
                />
              </div>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>{cov.covered}/{cov.total_requirements} requirements</span>
                <span>{cov.test_suites} suites</span>
                <span>Updated: {new Date(cov.last_generated).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
