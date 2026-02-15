'use client'

import { useState } from 'react'
import { Copy, GitCompare, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react'

interface ReferenceRepo {
  id: string
  name: string
  description: string
  languages: string[]
  frameworks: string[]
  complianceScore: number
  patternsCount: number
  industry: string
  verified: boolean
}

interface ComplianceGap {
  id: string
  category: string
  description: string
  severity: string
  suggestedFix: string
  estimatedEffortHours: number
  filesAffected: string[]
}

const MOCK_REFERENCE_REPOS: ReferenceRepo[] = [
  { id: 'ref-fintech-py', name: 'fintech-compliance-starter', description: 'Production-ready fintech backend with full PCI-DSS and SOX compliance.',
    languages: ['Python'], frameworks: ['FastAPI', 'SQLAlchemy'], complianceScore: 94.5, patternsCount: 28, industry: 'Fintech', verified: true },
  { id: 'ref-healthtech-ts', name: 'hipaa-saas-template', description: 'HIPAA-compliant SaaS template with ePHI handling and BAA tracking.',
    languages: ['TypeScript'], frameworks: ['Next.js', 'Prisma'], complianceScore: 91.2, patternsCount: 22, industry: 'Healthtech', verified: true },
  { id: 'ref-ai-platform', name: 'ai-compliance-platform', description: 'EU AI Act compliant ML platform with model cards and bias detection.',
    languages: ['Python'], frameworks: ['FastAPI', 'PyTorch'], complianceScore: 88.7, patternsCount: 19, industry: 'AI/ML', verified: true },
  { id: 'ref-ecommerce-java', name: 'gdpr-ecommerce-backend', description: 'GDPR-compliant e-commerce with consent management and data portability.',
    languages: ['Java'], frameworks: ['Spring Boot', 'Hibernate'], complianceScore: 92.1, patternsCount: 25, industry: 'E-commerce', verified: true },
]

const MOCK_GAPS: ComplianceGap[] = [
  { id: 'gap-1', category: 'encryption', description: 'Missing encryption at rest for user data', severity: 'critical',
    suggestedFix: 'Add Fernet encryption to all PII storage operations.', estimatedEffortHours: 4, filesAffected: ['src/models/user.py', 'src/db/storage.py'] },
  { id: 'gap-2', category: 'audit_logging', description: 'No structured audit logging for data access events', severity: 'high',
    suggestedFix: 'Implement structlog-based audit trail.', estimatedEffortHours: 6, filesAffected: ['src/middleware/audit.py'] },
  { id: 'gap-3', category: 'consent_management', description: 'No consent collection or tracking mechanism', severity: 'high',
    suggestedFix: 'Add consent management module.', estimatedEffortHours: 8, filesAffected: ['src/services/consent.py', 'src/api/consent.py'] },
  { id: 'gap-4', category: 'data_masking', description: 'API responses expose raw PII without masking', severity: 'medium',
    suggestedFix: 'Add response serializer with PII masking.', estimatedEffortHours: 3, filesAffected: ['src/api/serializers.py'] },
]

const severityColor = (s: string) => s === 'critical' ? 'text-red-600 bg-red-50' : s === 'high' ? 'text-orange-600 bg-orange-50' : 'text-yellow-600 bg-yellow-50'

export default function ComplianceCloningDashboard() {
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null)
  const [showPlan, setShowPlan] = useState(false)
  const [industryFilter, setIndustryFilter] = useState('all')

  const filtered = industryFilter === 'all' ? MOCK_REFERENCE_REPOS : MOCK_REFERENCE_REPOS.filter(r => r.industry.toLowerCase() === industryFilter.toLowerCase())
  const totalHours = MOCK_GAPS.reduce((sum, g) => sum + g.estimatedEffortHours, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><Copy className="h-7 w-7 text-teal-600" /> Compliance Cloning</h1>
        <p className="text-gray-500 mt-1">Clone compliance configurations from verified reference repositories</p>
      </div>

      {/* Score Before/After */}
      {showPlan && (
        <div className="bg-gradient-to-r from-red-50 to-green-50 rounded-lg border p-5 flex items-center justify-between">
          <div className="text-center">
            <div className="text-sm text-gray-500">Before</div>
            <div className="text-3xl font-bold text-red-600">45.2%</div>
          </div>
          <ArrowRight className="h-8 w-8 text-gray-400" />
          <div className="text-center">
            <div className="text-sm text-gray-500">After Cloning</div>
            <div className="text-3xl font-bold text-green-600">87.5%</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-500">Effort</div>
            <div className="text-3xl font-bold">{totalHours}h</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-500">Gaps</div>
            <div className="text-3xl font-bold">{MOCK_GAPS.length}</div>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2">
        {['all', 'Fintech', 'Healthtech', 'AI/ML', 'E-commerce'].map(ind => (
          <button key={ind} onClick={() => setIndustryFilter(ind)}
            className={`px-3 py-1 rounded-full text-sm ${industryFilter === ind ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-700'}`}>
            {ind}
          </button>
        ))}
      </div>

      {/* Reference Repos */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map(repo => (
          <div key={repo.id} className={`bg-white rounded-lg border p-5 cursor-pointer transition-all ${selectedRepo === repo.id ? 'ring-2 ring-teal-500' : 'hover:shadow-md'}`}
            onClick={() => { setSelectedRepo(repo.id); setShowPlan(true); }}>
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold">{repo.name}</h3>
                  {repo.verified && <CheckCircle className="h-4 w-4 text-green-500" />}
                </div>
                <p className="text-sm text-gray-600 mt-1">{repo.description}</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-green-600">{repo.complianceScore}%</div>
                <div className="text-xs text-gray-500">{repo.patternsCount} patterns</div>
              </div>
            </div>
            <div className="flex gap-2 mt-3">
              {repo.languages.map(l => <span key={l} className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded">{l}</span>)}
              {repo.frameworks.map(f => <span key={f} className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded">{f}</span>)}
              <span className="bg-purple-50 text-purple-700 text-xs px-2 py-0.5 rounded">{repo.industry}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Migration Plan */}
      {showPlan && (
        <div className="bg-white rounded-lg border">
          <div className="p-4 border-b flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2"><GitCompare className="h-5 w-5 text-teal-600" /> Migration Plan</h3>
            <button className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm hover:bg-teal-700">Apply All Fixes</button>
          </div>
          <div className="divide-y">
            {MOCK_GAPS.map(gap => (
              <div key={gap.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className={`h-4 w-4 ${gap.severity === 'critical' ? 'text-red-500' : gap.severity === 'high' ? 'text-orange-500' : 'text-yellow-500'}`} />
                    <span className="font-medium">{gap.description}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${severityColor(gap.severity)}`}>{gap.severity}</span>
                  </div>
                  <span className="text-sm text-gray-500">{gap.estimatedEffortHours}h</span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{gap.suggestedFix}</p>
                <div className="flex gap-1 mt-1">
                  {gap.filesAffected.map(f => <code key={f} className="text-xs bg-gray-50 px-1 rounded">{f}</code>)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
