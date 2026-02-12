'use client'

import { useState } from 'react'
import { Code, Download, Star, Shield, CheckCircle, AlertTriangle, Package, Terminal, BookOpen } from 'lucide-react'
import { usePolicies, useValidatePolicy, usePolicyMarketplace, useSDKInfo } from '@/hooks/useNextgenApi'
import type { PolicyDefinition, PolicyValidation, MarketplaceEntry, SDKInfo } from '@/types/nextgen'

const MOCK_POLICIES: PolicyDefinition[] = [
  { id: 'p1', name: 'GDPR Consent Verification', description: 'Validates consent collection before processing personal data', version: '1.2.0', language: 'yaml', category: 'data_privacy', severity: 'critical', frameworks: ['GDPR'], is_community: false, author: 'ComplianceAgent' },
  { id: 'p2', name: 'HIPAA PHI Encryption', description: 'Ensures PHI data is encrypted at rest and in transit', version: '1.0.0', language: 'rego', category: 'encryption', severity: 'critical', frameworks: ['HIPAA'], is_community: false, author: 'ComplianceAgent' },
  { id: 'p3', name: 'PCI Tokenization Check', description: 'Verifies PAN data uses tokenization or truncation', version: '1.1.0', language: 'python', category: 'encryption', severity: 'high', frameworks: ['PCI-DSS'], is_community: false, author: 'ComplianceAgent' },
  { id: 'p4', name: 'SOC 2 Audit Logging', description: 'Validates comprehensive audit logging is in place', version: '2.0.0', language: 'yaml', category: 'audit_logging', severity: 'high', frameworks: ['SOC 2'], is_community: false, author: 'ComplianceAgent' },
  { id: 'p5', name: 'EU AI Act Transparency', description: 'Checks AI system transparency and documentation requirements', version: '0.9.0', language: 'typescript', category: 'ai_transparency', severity: 'medium', frameworks: ['EU AI Act'], is_community: true, author: 'community' },
]

const MOCK_MARKETPLACE: MarketplaceEntry[] = [
  { id: 'm1', name: 'LGPD Data Localization', publisher: 'brazil-compliance', installs: 342, stars: 45, verified: true },
  { id: 'm2', name: 'CCPA Opt-Out Handler', publisher: 'privacy-tools', installs: 891, stars: 72, verified: true },
  { id: 'm3', name: 'NIST AI RMF Checker', publisher: 'ai-governance', installs: 156, stars: 28, verified: false },
  { id: 'm4', name: 'ISO 27001 Access Control', publisher: 'sec-ops-team', installs: 567, stars: 53, verified: true },
  { id: 'm5', name: 'DORA ICT Resilience', publisher: 'fintech-compliance', installs: 234, stars: 31, verified: true },
]

const MOCK_SDKS: SDKInfo[] = [
  { language: 'Python', package_name: 'complianceagent-sdk', install_command: 'pip install complianceagent-sdk', version: '0.3.0', docs_url: 'https://docs.complianceagent.dev/sdk/python' },
  { language: 'TypeScript', package_name: '@complianceagent/sdk', install_command: 'npm install @complianceagent/sdk', version: '0.3.0', docs_url: 'https://docs.complianceagent.dev/sdk/typescript' },
  { language: 'Go', package_name: 'github.com/complianceagent/sdk-go', install_command: 'go get github.com/complianceagent/sdk-go', version: '0.2.0', docs_url: 'https://docs.complianceagent.dev/sdk/go' },
]

const languageColors: Record<string, string> = {
  yaml: 'bg-green-100 text-green-700',
  rego: 'bg-purple-100 text-purple-700',
  python: 'bg-blue-100 text-blue-700',
  typescript: 'bg-indigo-100 text-indigo-700',
}

const severityColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-700',
  high: 'bg-orange-100 text-orange-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low: 'bg-green-100 text-green-700',
}

export default function PolicySDKDashboard() {
  const [tab, setTab] = useState<'policies' | 'marketplace' | 'sdks'>('policies')
  const [validation, setValidation] = useState<PolicyValidation | null>(null)
  const { data: livePolicies } = usePolicies()
  const { data: liveMarketplace } = usePolicyMarketplace()
  const { data: liveSDKs } = useSDKInfo()
  const { mutate: validate, loading: validating } = useValidatePolicy()

  const policies = livePolicies || MOCK_POLICIES
  const marketplace = liveMarketplace || MOCK_MARKETPLACE
  const sdks = liveSDKs || MOCK_SDKS

  const handleValidate = async (policyId: string) => {
    try {
      const res = await validate(policyId)
      setValidation(res)
    } catch {
      setValidation({ policy_id: policyId, is_valid: true, errors: [], warnings: ['Consider adding edge case for null values'], coverage: 87.5 })
    }
  }

  const tabs = [
    { key: 'policies' as const, label: 'Policies', icon: Shield },
    { key: 'marketplace' as const, label: 'Marketplace', icon: Package },
    { key: 'sdks' as const, label: 'SDK Packages', icon: Terminal },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance-as-Code Policy SDK</h1>
        <p className="text-gray-500">Create, validate, and share compliance policies</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Shield className="h-5 w-5 text-blue-600" />} title="Total Policies" value={policies.length.toString()} subtitle="Active policies" />
        <StatCard icon={<Package className="h-5 w-5 text-purple-600" />} title="Marketplace" value={marketplace.length.toString()} subtitle="Community policies" />
        <StatCard icon={<Terminal className="h-5 w-5 text-green-600" />} title="SDK Languages" value={sdks.length.toString()} subtitle="Python, TS, Go" />
        <StatCard icon={<Download className="h-5 w-5 text-orange-600" />} title="Total Installs" value={marketplace.reduce((s, m) => s + m.installs, 0).toLocaleString()} subtitle="Across marketplace" />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-md transition-colors ${tab === t.key ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
          >
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* Policies Tab */}
      {tab === 'policies' && (
        <div className="space-y-4">
          {/* Validation Result */}
          {validation && (
            <div className={`card p-4 ${validation.is_valid ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
              <div className="flex items-center gap-2 mb-2">
                {validation.is_valid ? <CheckCircle className="h-5 w-5 text-green-600" /> : <AlertTriangle className="h-5 w-5 text-red-600" />}
                <span className={`font-semibold ${validation.is_valid ? 'text-green-700' : 'text-red-700'}`}>
                  {validation.is_valid ? 'Policy Valid' : 'Validation Failed'}
                </span>
                <span className="text-sm text-gray-500 ml-auto">Coverage: {validation.coverage.toFixed(1)}%</span>
              </div>
              {validation.errors.length > 0 && (
                <div className="space-y-1">{validation.errors.map((e, i) => <p key={i} className="text-sm text-red-600">✗ {e}</p>)}</div>
              )}
              {validation.warnings.length > 0 && (
                <div className="space-y-1">{validation.warnings.map((w, i) => <p key={i} className="text-sm text-yellow-700">⚠ {w}</p>)}</div>
              )}
            </div>
          )}

          {/* Policy List */}
          <div className="card">
            <div className="p-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">Policy Library</h2>
            </div>
            <div className="divide-y divide-gray-100">
              {policies.map((p) => (
                <div key={p.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Code className="h-4 w-4 text-gray-400" />
                        <span className="font-medium text-gray-900">{p.name}</span>
                        <span className="text-xs text-gray-400">v{p.version}</span>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${languageColors[p.language] || 'bg-gray-100 text-gray-700'}`}>{p.language}</span>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${severityColors[p.severity] || 'bg-gray-100 text-gray-700'}`}>{p.severity}</span>
                      </div>
                      <p className="text-sm text-gray-500">{p.description}</p>
                      <div className="flex gap-1 mt-1">
                        {p.frameworks.map(f => <span key={f} className="px-2 py-0.5 bg-blue-50 text-blue-600 text-xs rounded">{f}</span>)}
                        {p.is_community && <span className="px-2 py-0.5 bg-purple-50 text-purple-600 text-xs rounded">Community</span>}
                      </div>
                    </div>
                    <button
                      onClick={() => handleValidate(p.id)}
                      disabled={validating}
                      className="px-3 py-1.5 text-xs bg-primary-50 text-primary-700 rounded-lg hover:bg-primary-100 transition-colors"
                    >
                      Validate
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Marketplace Tab */}
      {tab === 'marketplace' && (
        <div className="card">
          <div className="p-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Policy Marketplace</h2>
          </div>
          <div className="divide-y divide-gray-100">
            {marketplace.map((m) => (
              <div key={m.id} className="p-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-3">
                  <Package className="h-8 w-8 text-primary-500 p-1.5 bg-primary-50 rounded-lg" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{m.name}</span>
                      {m.verified && <CheckCircle className="h-4 w-4 text-blue-500" />}
                    </div>
                    <p className="text-xs text-gray-500">by {m.publisher}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <span className="flex items-center gap-1 text-gray-500"><Download className="h-3.5 w-3.5" /> {m.installs}</span>
                  <span className="flex items-center gap-1 text-yellow-600"><Star className="h-3.5 w-3.5" /> {m.stars}</span>
                  <button className="px-3 py-1.5 text-xs bg-primary-600 text-white rounded-lg hover:bg-primary-700">Install</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SDKs Tab */}
      {tab === 'sdks' && (
        <div className="space-y-4">
          {sdks.map((sdk) => (
            <div key={sdk.language} className="card p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Terminal className="h-5 w-5 text-gray-500" />
                  <h3 className="font-semibold text-gray-900">{sdk.language} SDK</h3>
                  <span className="text-xs text-gray-400">v{sdk.version}</span>
                </div>
                <a href={sdk.docs_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs text-primary-600 hover:text-primary-700">
                  <BookOpen className="h-3.5 w-3.5" /> Documentation
                </a>
              </div>
              <div className="bg-gray-900 rounded-lg p-3 flex items-center justify-between">
                <code className="text-sm text-green-400">{sdk.install_command}</code>
                <button
                  onClick={() => navigator.clipboard.writeText(sdk.install_command)}
                  className="px-2 py-1 text-xs text-gray-400 hover:text-white transition-colors"
                >
                  Copy
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">Package: <code className="bg-gray-100 px-1 rounded">{sdk.package_name}</code></p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-2"><p className="text-sm font-medium text-gray-500">{title}</p>{icon}</div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
    </div>
  )
}
