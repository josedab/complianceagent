'use client'

import { Network, Search, GitBranch, Database } from 'lucide-react'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface GraphNode {
  id: string
  type: string
  label: string
}

interface GraphStats {
  total_nodes: number
  total_edges: number
  frameworks: string[]
}

const FALLBACK_NODES: GraphNode[] = [
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

const FALLBACK_STATS: GraphStats = { total_nodes: 19, total_edges: 17, frameworks: ['GDPR', 'HIPAA', 'SOC 2'] }

const typeColors: Record<string, { bg: string; text: string }> = {
  framework: { bg: 'bg-blue-100', text: 'text-blue-700' },
  requirement: { bg: 'bg-purple-100', text: 'text-purple-700' },
  code_file: { bg: 'bg-green-100', text: 'text-green-700' },
  control: { bg: 'bg-orange-100', text: 'text-orange-700' },
  evidence: { bg: 'bg-gray-100', text: 'text-gray-700' },
}

export default function KnowledgeGraphDashboard() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<GraphNode[]>([])
  const [searched, setSearched] = useState(false)
  const [nodes, setNodes] = useState<GraphNode[]>(FALLBACK_NODES)
  const [stats, setStats] = useState<GraphStats>(FALLBACK_STATS)
  const [loading, setLoading] = useState(true)
  const [isDemo, setIsDemo] = useState(false)

  useEffect(() => {
    api.get('/knowledge-graph/stats')
      .then(res => {
        const data = res.data
        if (data && (data.total_nodes || data.nodes)) {
          setStats({
            total_nodes: Number(data.total_nodes ?? data.nodes ?? 0),
            total_edges: Number(data.total_edges ?? data.edges ?? data.relationships ?? 0),
            frameworks: data.frameworks || FALLBACK_STATS.frameworks,
          })
          if (data.sample_nodes && Array.isArray(data.sample_nodes)) {
            setNodes(data.sample_nodes)
          }
          setIsDemo(false)
        } else {
          setIsDemo(true)
        }
      })
      .catch(() => { setIsDemo(true) })
      .finally(() => setLoading(false))
  }, [])

  const handleSearch = () => {
    const q = query.toLowerCase()
    const filtered = nodes.filter(n => n.label.toLowerCase().includes(q) || n.type.includes(q))
    setResults(filtered)
    setSearched(true)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}
        </div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {isDemo && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-2 rounded-lg text-sm">
          Using demo data — connect backend for live data
        </div>
      )}

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
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats.total_nodes}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Relationships</p>
            <GitBranch className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats.total_edges}</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Frameworks</p>
            <Network className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats.frameworks.length}</p>
          <p className="mt-1 text-sm text-gray-500">{stats.frameworks.join(', ')}</p>
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
          {(searched ? results : nodes).map(node => {
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
