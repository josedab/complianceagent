'use client'

import { Globe, Code, Shield, Zap } from 'lucide-react'

const METHOD_COLORS: Record<string, string> = {
  GET: 'bg-green-100 text-green-700',
  POST: 'bg-blue-100 text-blue-700',
  PUT: 'bg-yellow-100 text-yellow-700',
  DELETE: 'bg-red-100 text-red-700',
}

const API_CATEGORIES = [
  {
    name: 'Core Pipeline',
    icon: 'code',
    endpoints: [
      { method: 'POST', path: '/api/v1/pipeline/run', description: 'Execute a compliance pipeline run' },
      { method: 'GET', path: '/api/v1/pipeline/status/{id}', description: 'Get pipeline run status' },
      { method: 'GET', path: '/api/v1/pipeline/history', description: 'List pipeline execution history' },
      { method: 'PUT', path: '/api/v1/pipeline/config', description: 'Update pipeline configuration' },
      { method: 'DELETE', path: '/api/v1/pipeline/run/{id}', description: 'Cancel a running pipeline' },
    ],
  },
  {
    name: 'AI Intelligence',
    icon: 'zap',
    endpoints: [
      { method: 'POST', path: '/api/v1/ai/analyze', description: 'Run AI-powered compliance analysis' },
      { method: 'POST', path: '/api/v1/ai/suggest', description: 'Get AI remediation suggestions' },
      { method: 'GET', path: '/api/v1/ai/models', description: 'List available AI models' },
      { method: 'POST', path: '/api/v1/ai/classify', description: 'Classify compliance violations' },
    ],
  },
  {
    name: 'Developer Tools',
    icon: 'code',
    endpoints: [
      { method: 'POST', path: '/api/v1/dev/lint', description: 'Lint code for compliance issues' },
      { method: 'GET', path: '/api/v1/dev/rules', description: 'List available compliance rules' },
      { method: 'POST', path: '/api/v1/dev/scan', description: 'Scan repository for violations' },
      { method: 'GET', path: '/api/v1/dev/sdk/config', description: 'Get SDK configuration' },
      { method: 'PUT', path: '/api/v1/dev/rules/{id}', description: 'Update a custom rule definition' },
      { method: 'POST', path: '/api/v1/dev/webhook', description: 'Register a webhook for events' },
    ],
  },
  {
    name: 'Certification & Audit',
    icon: 'shield',
    endpoints: [
      { method: 'POST', path: '/api/v1/audit/start', description: 'Start a new audit session' },
      { method: 'GET', path: '/api/v1/audit/reports', description: 'List generated audit reports' },
      { method: 'GET', path: '/api/v1/cert/status/{framework}', description: 'Get certification status for framework' },
      { method: 'POST', path: '/api/v1/cert/evidence', description: 'Submit certification evidence' },
      { method: 'GET', path: '/api/v1/audit/findings/{id}', description: 'Get detailed audit findings' },
    ],
  },
  {
    name: 'Platform & Enterprise',
    icon: 'globe',
    endpoints: [
      { method: 'GET', path: '/api/v1/org/settings', description: 'Get organization settings' },
      { method: 'PUT', path: '/api/v1/org/settings', description: 'Update organization settings' },
      { method: 'GET', path: '/api/v1/org/users', description: 'List organization users' },
      { method: 'POST', path: '/api/v1/org/invite', description: 'Invite user to organization' },
    ],
  },
  {
    name: 'Analytics & Scoring',
    icon: 'zap',
    endpoints: [
      { method: 'GET', path: '/api/v1/analytics/dashboard', description: 'Get dashboard analytics data' },
      { method: 'GET', path: '/api/v1/analytics/trends', description: 'Get compliance trend metrics' },
      { method: 'GET', path: '/api/v1/score/{repo}', description: 'Get compliance score for repository' },
      { method: 'POST', path: '/api/v1/score/calculate', description: 'Calculate compliance score on demand' },
      { method: 'GET', path: '/api/v1/analytics/export', description: 'Export analytics data as CSV' },
    ],
  },
]

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm text-gray-500">{title}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function APIExplorerDashboard() {
  const totalEndpoints = API_CATEGORIES.reduce((sum, cat) => sum + cat.endpoints.length, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">API Explorer</h1>
        <p className="text-gray-500">Browse and test all available compliance API endpoints</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Globe className="w-5 h-5 text-blue-500" />} title="API Categories" value="6" subtitle="Organized by domain" />
        <StatCard icon={<Code className="w-5 h-5 text-green-500" />} title="Total Endpoints" value={String(totalEndpoints)} subtitle="REST API v1" />
        <StatCard icon={<Shield className="w-5 h-5 text-purple-500" />} title="Auth Required" value="100%" subtitle="OAuth 2.0 + API Key" />
        <StatCard icon={<Zap className="w-5 h-5 text-orange-500" />} title="Avg Response" value="85ms" subtitle="p95 latency" />
      </div>

      <div className="space-y-4">
        {API_CATEGORIES.map((category) => (
          <div key={category.name} className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{category.name}</h2>
            <div className="space-y-2">
              {category.endpoints.map((endpoint, idx) => (
                <div key={idx} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
                  <span className={`px-2 py-1 rounded text-xs font-mono font-bold min-w-[60px] text-center ${METHOD_COLORS[endpoint.method]}`}>
                    {endpoint.method}
                  </span>
                  <code className="text-sm font-mono text-gray-700">{endpoint.path}</code>
                  <span className="text-sm text-gray-500 ml-auto">{endpoint.description}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
