'use client'

import { useState } from 'react'
import { Building2, AlertTriangle, TrendingUp } from 'lucide-react'
import { useAnalyzeArchitecture } from '@/hooks/useNextgenApi'
import type { DesignReviewResult, RiskSeverity } from '@/types/nextgen'

const MOCK_REVIEW: DesignReviewResult = {
  id: 'review-001',
  repo: 'acme/payments-api',
  detected_patterns: [
    { pattern_type: 'microservices', confidence: 0.85, evidence: ['docker-compose.yml', 'k8s/'], description: 'Docker Compose + Kubernetes detected' },
    { pattern_type: 'event_driven', confidence: 0.72, evidence: ['celery/', 'events/'], description: 'Celery task queue detected' },
  ],
  risks: [
    { id: 'r1', pattern: 'microservices', regulation: 'PCI-DSS', severity: 'medium', title: 'Service-to-service card data exposure', description: 'Internal APIs may transmit card data in plaintext', affected_components: ['payment-service', 'billing-service'], recommendation: 'Implement mTLS for all inter-service communication' },
    { id: 'r2', pattern: 'event_driven', regulation: 'HIPAA', severity: 'high', title: 'Event streams may leak PHI', description: 'Message queues may expose PHI without encryption', affected_components: ['celery/'], recommendation: 'Enable TLS and encrypt PHI fields in event payloads' },
  ],
  recommendations: [
    { id: 'rec1', title: 'PHI Encryption Gateway', description: 'Route all PHI through a dedicated encryption gateway', regulation: 'HIPAA', current_pattern: 'event_driven', recommended_pattern: 'encryption_gateway', effort_estimate_days: 20, impact: 'critical', trade_offs: ['Single point of failure risk', 'Key management complexity'] },
    { id: 'rec2', title: 'Card Data Isolation Segment', description: 'Isolate card data into a separate network segment', regulation: 'PCI-DSS', current_pattern: 'microservices', recommended_pattern: 'network_segmentation', effort_estimate_days: 25, impact: 'critical', trade_offs: ['Network complexity', 'Deployment overhead'] },
  ],
  score: { overall_score: 72, data_isolation_score: 75, encryption_score: 65, audit_trail_score: 80, access_control_score: 70, data_flow_score: 70, max_score: 100, grade: 'C', risks_found: 2, recommendations_count: 2 },
  regulations_analyzed: ['GDPR', 'HIPAA', 'PCI-DSS'],
}

const severityColors: Record<RiskSeverity, string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-green-100 text-green-700',
  info: 'bg-blue-100 text-blue-700',
}

const gradeColors: Record<string, string> = {
  A: 'text-green-600', B: 'text-blue-600', C: 'text-yellow-600', D: 'text-orange-600', F: 'text-red-600',
}

export default function ArchitectureAdvisorDashboard() {
  const [review, setReview] = useState<DesignReviewResult>(MOCK_REVIEW)
  const { mutate: analyzeArch, loading: analyzing } = useAnalyzeArchitecture()
  const score = review.score

  const handleAnalyze = async () => {
    try {
      const result = await analyzeArch({ repo: review.repo })
      setReview(result)
    } catch {
      // Keep mock data on error
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Architecture Advisor</h1>
          <p className="text-gray-500">Compliance-aware architecture analysis for {review.repo}</p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {analyzing ? 'Analyzing...' : 'Re-Analyze'}
        </button>
      </div>

      {/* Score Overview */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
        <div className="md:col-span-2 card flex flex-col items-center justify-center">
          <p className="text-sm text-gray-500 mb-2">Overall Grade</p>
          <p className={`text-6xl font-bold ${gradeColors[score.grade] || 'text-gray-600'}`}>{score.grade}</p>
          <p className="text-2xl font-semibold text-gray-700 mt-1">{score.overall_score}/100</p>
        </div>
        <ScoreCard title="Data Isolation" value={score.data_isolation_score} />
        <ScoreCard title="Encryption" value={score.encryption_score} />
        <ScoreCard title="Audit Trail" value={score.audit_trail_score} />
        <ScoreCard title="Access Control" value={score.access_control_score} />
      </div>

      {/* Detected Patterns */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Detected Patterns</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {review.detected_patterns.map((p, i) => (
            <div key={i} className="p-3 rounded-lg border border-gray-100">
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900 capitalize">{p.pattern_type.replace('_', ' ')}</span>
                <span className="text-sm text-gray-500">{(p.confidence * 100).toFixed(0)}% confidence</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">{p.description}</p>
              <div className="flex gap-1 mt-2">
                {p.evidence.map(e => <span key={e} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">{e}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Risks */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <h2 className="text-lg font-semibold text-gray-900">Compliance Risks ({review.risks.length})</h2>
        </div>
        <div className="space-y-3">
          {review.risks.map(risk => (
            <div key={risk.id} className="p-4 rounded-lg border border-gray-100">
              <div className="flex items-center gap-2 mb-2">
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${severityColors[risk.severity]}`}>{risk.severity}</span>
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">{risk.regulation}</span>
                <span className="font-medium text-gray-900">{risk.title}</span>
              </div>
              <p className="text-sm text-gray-500">{risk.description}</p>
              <div className="mt-2 p-2 bg-green-50 rounded text-sm text-green-800">
                💡 {risk.recommendation}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-5 w-5 text-green-500" />
          <h2 className="text-lg font-semibold text-gray-900">Recommendations</h2>
        </div>
        <div className="space-y-3">
          {review.recommendations.map(rec => (
            <div key={rec.id} className="p-4 rounded-lg border border-gray-100">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900">{rec.title}</span>
                <span className="text-sm text-gray-500">{rec.effort_estimate_days} dev-days</span>
              </div>
              <p className="text-sm text-gray-500">{rec.description}</p>
              <div className="flex gap-2 mt-2">
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">{rec.regulation}</span>
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${severityColors[rec.impact]}`}>Impact: {rec.impact}</span>
              </div>
              {rec.trade_offs.length > 0 && (
                <div className="mt-2 text-xs text-gray-400">
                  Trade-offs: {rec.trade_offs.join(' · ')}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function ScoreCard({ title, value }: { title: string; value: number }) {
  const color = value >= 80 ? 'text-green-600' : value >= 60 ? 'text-yellow-600' : 'text-red-600'
  return (
    <div className="card">
      <p className="text-sm font-medium text-gray-500">{title}</p>
      <p className={`mt-2 text-3xl font-bold ${color}`}>{value}</p>
      <div className="mt-2 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${value >= 80 ? 'bg-green-500' : value >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}
