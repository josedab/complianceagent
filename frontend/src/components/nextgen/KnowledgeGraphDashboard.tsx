'use client'

import { Network, Search, GitBranch, Database } from 'lucide-react'
import { useState } from 'react'

const MOCK_NODES = [
  { id: '1', type: 'framework', label: 'GDPR' },
  { id: '2', type: 'framework', label: 'HIPAA' },
  { id: '3', type: 'framework', label: 'SOC 2' },
  { id: '4', type: 'requirement', label: 'Art.17 Right to Erasure' },
  { id: '5', type: 'requirement', label: 'Art.7 Consent' },
  { id: '6', type: 'requirement', label: '§164.312 Technical Safeguards' },
  { id: '7', type: 'requirement', label: 'CC6.1 Access Controls' },
  { id: '8', type: 'code_file', label: 'src/api/users.py' },
  { id: '9', type: 'code_file', label: 'src/auth/login.py' },
  { id: '10', type: 'control', label: 'Encryption at Rest' },
  { id: '11', type: 'control', label: 'MFA Authentication' },
  { id: '12', type: 'evidence', label: 'Encryption config audit' },
]

const MOCK_STATS = { total_nodes: 19, total_edges: 17, frameworks: ['GDPR', 'HIPAA', 'SOC 2'] }

const typeColors: Record<string, { bg: string; text: string }> = {
  framework: { bg: 'bg-blue-100', text: 'text-blue-700' },
  requirement: { bg: 'bg-purple-100', text: 'text-purple-700' },
  code_file: { bg: 'bg-green-100', text: 'text-green-700' },
  control: { bg: 'bg-orange-100', text: 'text-orange-700' },
  evidence: { bg: 'bg-gray-100', text: 'text-gray-700' },
}

export default function KnowledgeGraphDashboard() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<typeof MOCK_NODES>([])
  const [searched, setSearched] = useState(false)

  const handleSearch = () => {
    const q = query.toLowerCase()
    const filtered = MOCK_NODES.filter(n => n.label.toLowerCase().includes(q) || n.type.includes(q))
    setResults(filtered)
    setSearched(true)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Knowledge Graph</h1>
        <p className="text-gray-500">Navigate compliance relationships with natural language queries</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Nodes</p>
            <Database className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{MOCK_STATS.total_nodes}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Relationships</p>
            <GitBranch className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{MOCK_STATS.total_edges}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Frameworks</p>
            <Network className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{MOCK_STATS.frameworks.length}</p>
          <p className="mt-1 text-sm text-gray-500">{MOCK_STATS.frameworks.join(', ')}</p>
        </div>
      </div>

      {/* Search */}
      <div className="card">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="Search: e.g. 'GDPR erasure', 'encryption controls', 'HIPAA'"
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button onClick={handleSearch} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Query Graph
          </button>
        </div>
      </div>

      {/* Results or default view */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {searched ? `Results for "${query}"` : 'Graph Nodes'}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {(searched ? results : MOCK_NODES).map(node => {
            const colors = typeColors[node.type] || typeColors.evidence
            return (
              <div key={node.id} className="p-3 border rounded-lg hover:shadow-sm transition-shadow">
                <span className={`text-xs px-2 py-0.5 rounded-full ${colors.bg} ${colors.text}`}>
                  {node.type}
                </span>
                <p className="mt-2 font-medium text-gray-900">{node.label}</p>
              </div>
            )
          })}
          {searched && results.length === 0 && (
            <p className="text-gray-500 col-span-full text-center py-8">No nodes match your query.</p>
          )}
        </div>
      </div>
    </div>
  )
}
