'use client'

import { useState } from 'react'
import { Code, Search, ThumbsUp, ThumbsDown, Brain, Zap, MessageSquare } from 'lucide-react'
import { useRAGSearch, useFeedbackStats } from '@/hooks/useNextgenApi'
import type { RAGSearchResult } from '@/types/nextgen'

export default function IdeCopilotDashboard() {
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<RAGSearchResult[]>([])
  const { mutate: ragSearch, loading: searching } = useRAGSearch()
  const { data: stats, loading: statsLoading, error: statsError, refetch: refetchStats } = useFeedbackStats()

  const handleSearch = async () => {
    if (!query.trim()) return
    const results = await ragSearch({ query, top_k: 5 })
    setSearchResults(results)
  }

  if (statsLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
        </div>
        <div className="card h-48 animate-pulse bg-gray-100" />
      </div>
    )
  }

  if (statsError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading IDE Co-Pilot: {statsError.message}</p>
        <button onClick={refetchStats} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
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
          <p className="mt-2 text-3xl font-bold text-gray-900">{stats?.total_feedback ?? 0}</p>
          <p className="mt-1 text-sm text-gray-500">Suggestions rated</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Helpful Rate</p>
            <ThumbsUp className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">
            {stats ? Math.round(stats.helpful_count / Math.max(stats.total_feedback, 1) * 100) : 0}%
          </p>
          <p className="mt-1 text-sm text-gray-500">{stats?.helpful_count ?? 0} helpful</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Application Rate</p>
            <Zap className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">
            {stats ? Math.round(stats.application_rate * 100) : 0}%
          </p>
          <p className="mt-1 text-sm text-gray-500">Fixes applied</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Incorrect</p>
            <ThumbsDown className="h-5 w-5 text-red-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-red-600">{stats?.incorrect_count ?? 0}</p>
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

        {searchResults.length === 0 ? (
          <p className="text-gray-400 text-sm">Enter a query above to search regulations.</p>
        ) : (
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
        )}
      </div>
    </div>
  )
}
