'use client'

import { useState } from 'react'
import { Code, Search, ThumbsUp, ThumbsDown, Brain, Zap, MessageSquare } from 'lucide-react'
import { useRAGSearch, useFeedbackStats } from '@/hooks/useNextgenApi'
import type { RAGSearchResult, FeedbackStats } from '@/types/nextgen'

const MOCK_RESULTS: RAGSearchResult[] = [
  { regulation: 'GDPR', article: 'Art. 25', text: 'The controller shall implement appropriate technical and organisational measures for ensuring data protection by design and by default.', relevance_score: 0.95, metadata: {} },
  { regulation: 'GDPR', article: 'Art. 32', text: 'The controller and processor shall implement appropriate technical measures to ensure a level of security appropriate to the risk, including encryption.', relevance_score: 0.87, metadata: {} },
  { regulation: 'HIPAA', article: '§164.312(a)', text: 'Implement technical policies and procedures for electronic information systems that maintain ePHI to allow access only to authorized persons.', relevance_score: 0.72, metadata: {} },
]

const MOCK_STATS: FeedbackStats = {
  total_feedback: 156,
  helpful_count: 112,
  not_helpful_count: 28,
  incorrect_count: 16,
  application_rate: 0.72,
  top_appreciated_rules: ['GDPR-PII-001', 'HIPAA-ENC-003'],
  top_rejected_rules: ['SOC2-LOG-012'],
}

export default function IdeCopilotDashboard() {
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<RAGSearchResult[]>(MOCK_RESULTS)
  const { mutate: ragSearch, loading: searching } = useRAGSearch()
  const { data: liveStats } = useFeedbackStats()
  const stats = liveStats || MOCK_STATS

  const handleSearch = async () => {
    if (!query.trim()) return
    try {
      const results = await ragSearch({ query, top_k: 5 })
      setSearchResults(results)
    } catch {
      setSearchResults(MOCK_RESULTS)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">IDE Compliance Co-Pilot</h1>
        <p className="text-gray-500">AI-powered compliance assistance with RAG regulation search and learning feedback</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Total Feedback</p>
            <MessageSquare className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats.total_feedback}</p>
          <p className="mt-1 text-sm text-gray-500">Suggestions rated</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Helpful Rate</p>
            <ThumbsUp className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{Math.round(stats.helpful_count / Math.max(stats.total_feedback, 1) * 100)}%</p>
          <p className="mt-1 text-sm text-gray-500">{stats.helpful_count} helpful</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Application Rate</p>
            <Zap className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">{Math.round(stats.application_rate * 100)}%</p>
          <p className="mt-1 text-sm text-gray-500">Fixes applied</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Incorrect</p>
            <ThumbsDown className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{stats.incorrect_count}</p>
          <p className="mt-1 text-sm text-gray-500">Marked incorrect</p>
        </div>
      </div>

      {/* RAG Search */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="h-5 w-5 text-purple-500" />
          <h2 className="text-lg font-semibold text-gray-900">Regulation RAG Search</h2>
        </div>
        <div className="flex gap-2 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="Search regulations... e.g. 'data encryption personal data'"
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <button onClick={handleSearch} disabled={searching} className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50">
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>

        <div className="space-y-3">
          {searchResults.map((result, i) => (
            <div key={i} className="p-4 rounded-lg border border-gray-100 hover:border-primary-200 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Code className="h-4 w-4 text-blue-500" />
                  <span className="font-medium text-gray-900">{result.regulation}</span>
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">{result.article}</span>
                </div>
                <span className="text-sm text-gray-400">Relevance: {Math.round(result.relevance_score * 100)}%</span>
              </div>
              <p className="text-sm text-gray-600">{result.text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
