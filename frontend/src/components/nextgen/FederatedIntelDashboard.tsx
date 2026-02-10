'use client'

import { Globe, Users, AlertTriangle, BarChart3, Shield } from 'lucide-react'
import { useThreatFeed, useIndustryBenchmarks } from '@/hooks/useNextgenApi'
import type { ComplianceThreat, IndustryBenchmark, RiskSeverity } from '@/types/nextgen'

const MOCK_THREATS: ComplianceThreat[] = [
  { id: 't1', title: 'EU AI Act Enforcement Wave', description: 'First enforcement actions expected for non-compliant AI systems', category: 'enforcement_action', severity: 'critical', regulations: ['EU_AI_ACT'], industries: ['ai_company', 'fintech'], verified: true },
  { id: 't2', title: 'GDPR Cross-Border Transfer Rules Updated', description: 'New SCCs required for US data transfers', category: 'regulatory_change', severity: 'high', regulations: ['GDPR'], industries: ['saas', 'fintech', 'healthtech'], verified: true },
  { id: 't3', title: 'Healthcare Data Breach Pattern Detected', description: 'Spike in API-based PHI exposure incidents', category: 'data_breach_pattern', severity: 'high', regulations: ['HIPAA'], industries: ['healthtech'], verified: true },
  { id: 't4', title: 'India DPDP Compliance Deadline Approaching', description: 'Indian data protection law enforcement begins', category: 'emerging_regulation', severity: 'medium', regulations: ['DPDP'], industries: ['saas', 'ecommerce'], verified: false },
]

const MOCK_BENCHMARKS: IndustryBenchmark[] = [
  { industry: 'Fintech', avg_compliance_score: 78, common_frameworks: ['GDPR', 'PCI-DSS', 'SOX'], top_risks: ['Cross-border data transfers', 'Card data exposure'] },
  { industry: 'Healthtech', avg_compliance_score: 72, common_frameworks: ['HIPAA', 'GDPR', 'FDA'], top_risks: ['PHI encryption gaps', 'Breach notification timing'] },
  { industry: 'SaaS', avg_compliance_score: 68, common_frameworks: ['SOC 2', 'GDPR', 'CCPA'], top_risks: ['Data retention policies', 'Vendor risk management'] },
]

const severityColors: Record<RiskSeverity, string> = {
  critical: 'bg-red-100 text-red-700', high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700', low: 'bg-green-100 text-green-700',
  info: 'bg-blue-100 text-blue-700',
}

export default function FederatedIntelDashboard() {
  const { data: liveThreats } = useThreatFeed()
  const { data: liveBenchmarks } = useIndustryBenchmarks()

  const threats = liveThreats || MOCK_THREATS
  const benchmarks = liveBenchmarks ? Object.values(liveBenchmarks) : MOCK_BENCHMARKS

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Federated Compliance Intelligence</h1>
        <p className="text-gray-500">Privacy-preserving intelligence network with industry benchmarks</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Globe className="h-5 w-5 text-blue-600" />} title="Network Members" value="247" subtitle="Organizations sharing insights" />
        <StatCard icon={<AlertTriangle className="h-5 w-5 text-red-600" />} title="Active Threats" value={threats.length.toString()} subtitle={`${threats.filter(t => t.severity === 'critical').length} critical`} />
        <StatCard icon={<Shield className="h-5 w-5 text-green-600" />} title="Patterns Shared" value="189" subtitle="Compliance patterns" />
        <StatCard icon={<Users className="h-5 w-5 text-purple-600" />} title="Industries" value={benchmarks.length.toString()} subtitle="With benchmarks" />
      </div>

      {/* Threat Feed */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <h2 className="text-lg font-semibold text-gray-900">Threat Intelligence Feed</h2>
        </div>
        <div className="space-y-3">
          {threats.map(threat => (
            <div key={threat.id} className="p-4 rounded-lg border border-gray-100">
              <div className="flex items-center gap-2 mb-2">
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${severityColors[threat.severity]}`}>{threat.severity}</span>
                {threat.verified && <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">✓ Verified</span>}
                {threat.regulations.map(r => <span key={r} className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">{r}</span>)}
              </div>
              <p className="font-medium text-gray-900">{threat.title}</p>
              <p className="text-sm text-gray-500 mt-1">{threat.description}</p>
              <div className="flex gap-1 mt-2">
                {threat.industries.map(i => <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">{i}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Benchmarks */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Industry Benchmarks</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {benchmarks.map(bm => (
            <div key={bm.industry} className="p-4 rounded-lg border border-gray-100">
              <div className="flex items-center justify-between mb-3">
                <span className="font-medium text-gray-900">{bm.industry}</span>
                <span className={`text-lg font-bold ${bm.avg_compliance_score >= 75 ? 'text-green-600' : bm.avg_compliance_score >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {bm.avg_compliance_score}%
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-3">
                <div className={`h-full rounded-full ${bm.avg_compliance_score >= 75 ? 'bg-green-500' : bm.avg_compliance_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${bm.avg_compliance_score}%` }} />
              </div>
              <div className="space-y-2">
                <div>
                  <p className="text-xs text-gray-400">Frameworks</p>
                  <div className="flex gap-1 flex-wrap">
                    {bm.common_frameworks.map(f => <span key={f} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">{f}</span>)}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-gray-400">Top Risks</p>
                  {bm.top_risks.map(r => <p key={r} className="text-xs text-gray-600">• {r}</p>)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between"><p className="text-sm font-medium text-gray-500">{title}</p>{icon}</div>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
    </div>
  )
}
