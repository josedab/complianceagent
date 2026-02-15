'use client'

import { useState } from 'react'
import { DollarSign, Code, Zap } from 'lucide-react'

interface ComplianceAPI {
  id: string
  name: string
  description: string
  endpoint: string
  regulation: string
  version: string
  requestsPerMonth: number
  avgLatencyMs: number
  pricingPerRequest: number
  supportedLanguages: string[]
  tags: string[]
}

const MOCK_APIS: ComplianceAPI[] = [
  { id: 'check-gdpr', name: 'Check GDPR Compliance', description: 'Analyze code for GDPR violations including consent, data minimization, and retention.',
    endpoint: '/api/check/gdpr', regulation: 'GDPR', version: '1.2.0', requestsPerMonth: 45200, avgLatencyMs: 120, pricingPerRequest: 0.02,
    supportedLanguages: ['Python', 'TypeScript', 'Java', 'Go'], tags: ['privacy', 'gdpr', 'pii'] },
  { id: 'validate-hipaa', name: 'Validate HIPAA PHI', description: 'Detect PHI in code and data flows with remediation suggestions.',
    endpoint: '/api/check/hipaa', regulation: 'HIPAA', version: '1.1.0', requestsPerMonth: 28700, avgLatencyMs: 145, pricingPerRequest: 0.03,
    supportedLanguages: ['Python', 'TypeScript', 'Java'], tags: ['healthcare', 'phi', 'hipaa'] },
  { id: 'assess-pci', name: 'Assess PCI-DSS', description: 'Evaluate payment processing code for PCI-DSS compliance.',
    endpoint: '/api/check/pci-dss', regulation: 'PCI-DSS', version: '1.0.0', requestsPerMonth: 19500, avgLatencyMs: 160, pricingPerRequest: 0.025,
    supportedLanguages: ['Python', 'TypeScript', 'Java', 'Go', 'Ruby'], tags: ['payment', 'pci'] },
  { id: 'detect-ai-bias', name: 'Detect AI Bias', description: 'Analyze ML models for bias, fairness, and EU AI Act compliance.',
    endpoint: '/api/check/ai-bias', regulation: 'EU AI Act', version: '0.9.0', requestsPerMonth: 8900, avgLatencyMs: 250, pricingPerRequest: 0.05,
    supportedLanguages: ['Python'], tags: ['ai', 'bias', 'fairness'] },
  { id: 'scan-soc2', name: 'Scan SOC 2 Controls', description: 'Verify SOC 2 Type II control implementation across code.',
    endpoint: '/api/check/soc2', regulation: 'SOC 2', version: '1.0.0', requestsPerMonth: 15300, avgLatencyMs: 180, pricingPerRequest: 0.03,
    supportedLanguages: ['Python', 'TypeScript', 'Go'], tags: ['audit', 'soc2'] },
]

const MOCK_REVENUE = {
  totalApis: 5, totalDevelopers: 342, totalRequestsMonth: 117600,
  monthlyRevenue: 48500, topApi: 'check-gdpr', revenueGrowth: 23.5, avgRevenuePerApi: 9700,
}

const PRICING_TIERS = [
  { name: 'Free', price: '$0', requests: '100/mo', features: ['1 API', 'Community support'] },
  { name: 'Starter', price: '$99', requests: '5,000/mo', features: ['All APIs', 'Email support', 'Usage analytics'] },
  { name: 'Pro', price: '$499', requests: '50,000/mo', features: ['All APIs', 'Priority support', 'Custom rules', 'Webhooks'] },
  { name: 'Enterprise', price: 'Custom', requests: '500,000+/mo', features: ['Dedicated instance', 'SLA', 'Custom integrations'] },
]

export default function APIMonetizationDashboard() {
  const [selectedApi, setSelectedApi] = useState<string | null>(null)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><DollarSign className="h-7 w-7 text-emerald-600" /> API Monetization</h1>
        <p className="text-gray-500 mt-1">Monetizable compliance check APIs with usage-based billing</p>
      </div>

      {/* Revenue Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-emerald-50 rounded-lg border border-emerald-200 p-4">
          <div className="text-sm text-emerald-600 flex items-center gap-1"><DollarSign className="h-3 w-3" />Monthly Revenue</div>
          <div className="text-2xl font-bold text-emerald-700">${MOCK_REVENUE.monthlyRevenue.toLocaleString()}</div>
          <div className="text-xs text-emerald-500">+{MOCK_REVENUE.revenueGrowth}% growth</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Developers</div>
          <div className="text-2xl font-bold">{MOCK_REVENUE.totalDevelopers}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Requests/Month</div>
          <div className="text-2xl font-bold">{(MOCK_REVENUE.totalRequestsMonth / 1000).toFixed(1)}K</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Avg Revenue/API</div>
          <div className="text-2xl font-bold">${MOCK_REVENUE.avgRevenuePerApi.toLocaleString()}</div>
        </div>
      </div>

      {/* API Catalog */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">API Catalog</h2>
        {MOCK_APIS.map(api => (
          <div key={api.id} className="bg-white rounded-lg border p-5 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => setSelectedApi(selectedApi === api.id ? null : api.id)}>
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Code className="h-4 w-4 text-gray-500" />
                  <h3 className="font-semibold">{api.name}</h3>
                  <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">v{api.version}</span>
                  <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{api.regulation}</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{api.description}</p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-emerald-600">${api.pricingPerRequest}/req</div>
                <div className="text-xs text-gray-500">{(api.requestsPerMonth / 1000).toFixed(1)}K req/mo</div>
              </div>
            </div>
            <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
              <span className="flex items-center gap-1"><Zap className="h-3 w-3" />{api.avgLatencyMs}ms</span>
              <span className="flex items-center gap-1"><Code className="h-3 w-3" />{api.supportedLanguages.join(', ')}</span>
            </div>
            {selectedApi === api.id && (
              <div className="mt-4 pt-4 border-t">
                <div className="bg-gray-900 rounded p-3 text-sm">
                  <div className="text-gray-400 mb-1"># Example usage</div>
                  <code className="text-green-400">curl -X POST {api.endpoint} \</code><br/>
                  <code className="text-green-400">&nbsp;&nbsp;-H &quot;Authorization: Bearer $API_KEY&quot; \</code><br/>
                  <code className="text-green-400">&nbsp;&nbsp;-d &apos;{`{"code": "...", "language": "python"}`}&apos;</code>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Pricing Tiers */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Pricing Tiers</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {PRICING_TIERS.map(tier => (
            <div key={tier.name} className={`bg-white rounded-lg border p-5 ${tier.name === 'Pro' ? 'ring-2 ring-emerald-500' : ''}`}>
              <h3 className="font-semibold">{tier.name}</h3>
              <div className="text-2xl font-bold mt-2">{tier.price}<span className="text-sm text-gray-500 font-normal">/mo</span></div>
              <div className="text-sm text-gray-500 mt-1">{tier.requests}</div>
              <ul className="mt-3 space-y-1">
                {tier.features.map(f => <li key={f} className="text-sm text-gray-600 flex items-center gap-1">✓ {f}</li>)}
              </ul>
              <button className={`w-full mt-4 py-2 rounded text-sm ${tier.name === 'Pro' ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-700'}`}>
                {tier.name === 'Enterprise' ? 'Contact Sales' : 'Subscribe'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
