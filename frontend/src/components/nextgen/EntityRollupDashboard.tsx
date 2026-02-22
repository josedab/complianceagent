'use client'

import { Building2, Users, Shield } from 'lucide-react'

const MOCK_HIERARCHY = [
  { id: '1', name: 'Acme Corp', level: 0, score: 85.0, aggregated: 84.2, frameworks: ['GDPR', 'SOC 2', 'HIPAA'], members: 500, children: [
    { id: '2', name: 'Engineering', level: 1, score: 88.0, aggregated: 85.5, frameworks: ['GDPR', 'SOC 2'], members: 200, children: [
      { id: '4', name: 'Platform Team', level: 2, score: 92.0, frameworks: ['GDPR', 'SOC 2'], members: 30 },
      { id: '5', name: 'Data Team', level: 2, score: 78.0, frameworks: ['GDPR', 'HIPAA'], members: 15 },
    ]},
    { id: '3', name: 'Finance', level: 1, score: 82.0, aggregated: 82.0, frameworks: ['SOX', 'PCI-DSS'], members: 50, children: [] },
  ]},
]

const scoreColor = (score: number) => {
  if (score >= 85) return 'text-green-600'
  if (score >= 70) return 'text-yellow-600'
  return 'text-red-600'
}

const scoreBg = (score: number) => {
  if (score >= 85) return 'bg-green-50 border-green-200'
  if (score >= 70) return 'bg-yellow-50 border-yellow-200'
  return 'bg-red-50 border-red-200'
}

interface EntityData {
  id: string
  name: string
  level: number
  score: number
  aggregated?: number
  frameworks: string[]
  members: number
  children?: EntityData[]
}

function EntityCard({ entity, depth = 0 }: { entity: EntityData; depth?: number }) {
  return (
    <div className="space-y-2">
      <div className={`p-4 rounded-lg border ${scoreBg(entity.score)}`} style={{ marginLeft: depth * 24 }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Building2 className="h-5 w-5 text-gray-400" />
            <div>
              <h3 className="font-semibold text-gray-900">{entity.name}</h3>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Users className="h-3.5 w-3.5" />
                <span>{entity.members} members</span>
                <span>•</span>
                <span>{entity.frameworks.join(', ')}</span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className={`text-2xl font-bold ${scoreColor(entity.score)}`}>{entity.score}%</p>
            {entity.aggregated && entity.aggregated !== entity.score && (
              <p className="text-xs text-gray-400">Aggregated: {entity.aggregated}%</p>
            )}
          </div>
        </div>
      </div>
      {entity.children?.map((child: EntityData) => (
        <EntityCard key={child.id} entity={child} depth={depth + 1} />
      ))}
    </div>
  )
}

export default function EntityRollupDashboard() {
  const root = MOCK_HIERARCHY[0]
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Multi-Entity Compliance Rollup</h1>
        <p className="text-gray-500">Aggregated compliance scoring across your organization hierarchy</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Overall Score</p>
            <Shield className="h-5 w-5 text-blue-600" />
          </div>
          <p className={`mt-2 text-3xl font-bold ${scoreColor(root.aggregated)}`}>{root.aggregated}%</p>
          <p className="mt-1 text-sm text-gray-500">Weighted by team size</p>
        </div>
        <div className="card">
          <p className="text-sm font-medium text-gray-500">Total Members</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{root.members}</p>
        </div>
        <div className="card">
          <p className="text-sm font-medium text-gray-500">Entities</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">5</p>
          <p className="mt-1 text-sm text-gray-500">across 3 levels</p>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Organization Hierarchy</h2>
        <EntityCard entity={root} />
      </div>
    </div>
  )
}
