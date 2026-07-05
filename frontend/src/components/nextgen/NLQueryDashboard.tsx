'use client'

import { useState } from 'react'
import { MessageSquare, Send, ThumbsUp, ThumbsDown, Clock, Code, FileText, Sparkles } from 'lucide-react'
import { useNLQuery, useQueryHistory, useQueryFeedback } from '@/hooks/useNextgenApi'
import type { QueryResult } from '@/types/nextgen'

const SUGGESTED_QUERIES = [
  'What GDPR requirements affect user deletion?',
  'Which files handle PCI-DSS tokenization?',
  'Show HIPAA compliance status for patient data',
  'What are the EU AI Act transparency requirements?',
  'Compare SOC 2 vs ISO 27001 audit logging controls',
]

const intentColors: Record<string, string> = {
  regulation_lookup: 'bg-blue-100 text-blue-700',
  code_search: 'bg-purple-100 text-purple-700',
  violation_check: 'bg-red-100 text-red-700',
  audit_query: 'bg-green-100 text-green-700',
  status_report: 'bg-yellow-100 text-yellow-700',
  comparison: 'bg-indigo-100 text-indigo-700',
  recommendation: 'bg-orange-100 text-orange-700',
}

export default function NLQueryDashboard() {
  const [queryText, setQueryText] = useState('')
  const [result, setResult] = useState<QueryResult | null>(null)
  const { data: liveHistory, loading: historyLoading, error: historyError, refetch: refetchHistory } = useQueryHistory()
  const { mutate: executeQuery, loading: querying } = useNLQuery()
  const { mutate: submitFeedback } = useQueryFeedback()

  const history = liveHistory ?? []

  const handleQuery = async () => {
    if (!queryText.trim() || querying) return
    const res = await executeQuery({ query: queryText.trim() })
    setResult(res)
  }

  if (historyLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="card h-24 animate-pulse bg-gray-100" />
        <div className="card h-48 animate-pulse bg-gray-100" />
      </div>
    )
  }

  if (historyError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading Compliance Query Engine: {historyError.message}</p>
        <button onClick={refetchHistory} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Query Engine</h1>
        <p className="text-gray-500">Ask compliance questions in natural language</p>
      </div>

      {/* Query Input */}
      <div className="card p-4">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <MessageSquare className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
              placeholder="Ask a compliance question..."
              className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-200 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>
          <button
            onClick={handleQuery}
            disabled={querying || !queryText.trim()}
            className="px-4 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
          >
            {querying ? <Sparkles className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Ask
          </button>
        </div>

        {/* Suggested Queries */}
        {!result && (
          <div className="mt-3 flex flex-wrap gap-2">
            {SUGGESTED_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => { setQueryText(q); }}
                className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-primary-50 hover:text-primary-700 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Query Result */}
      {result && (
        <div className="card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${intentColors[result.intent] || 'bg-gray-100 text-gray-700'}`}>
                {result.intent.replace('_', ' ')}
              </span>
              <span className="text-sm text-gray-500">Confidence: {(result.confidence * 100).toFixed(0)}%</span>
              <span className="text-sm text-gray-400">({result.processing_time_ms.toFixed(0)}ms)</span>
            </div>
            <div className="flex gap-1">
              <button onClick={() => submitFeedback({ query_id: result.id, helpful: true })} className="p-1.5 rounded hover:bg-green-50 text-gray-400 hover:text-green-600">
                <ThumbsUp className="h-4 w-4" />
              </button>
              <button onClick={() => submitFeedback({ query_id: result.id, helpful: false })} className="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-600">
                <ThumbsDown className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Answer */}
          <div className="prose prose-sm max-w-none text-gray-700">
            <p>{result.answer}</p>
          </div>

          {/* Sources */}
          {result.sources.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-1">
                <FileText className="h-4 w-4" /> Sources
              </h4>
              <div className="space-y-2">
                {result.sources.map((s, i) => (
                  <div key={i} className="p-2 bg-blue-50 rounded-lg text-sm">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-blue-900">{s.title}</span>
                      <span className="text-xs text-blue-600">{(s.relevance_score * 100).toFixed(0)}% relevant</span>
                    </div>
                    <p className="text-blue-700 mt-1 text-xs">{s.snippet}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Code References */}
          {result.code_references.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-1">
                <Code className="h-4 w-4" /> Code References
              </h4>
              <div className="space-y-2">
                {result.code_references.map((c, i) => (
                  <div key={i} className="p-2 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-mono text-gray-700">{c.file_path}:{c.line_start}-{c.line_end}</span>
                      <span className="text-xs text-gray-500">{c.language}</span>
                    </div>
                    <pre className="text-xs bg-gray-900 text-green-400 p-2 rounded overflow-x-auto">{c.snippet}</pre>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Follow-up Suggestions */}
          {result.follow_up_suggestions.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100">
              {result.follow_up_suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => { setQueryText(s); setResult(null); }}
                  className="px-3 py-1 text-xs bg-primary-50 text-primary-700 rounded-full hover:bg-primary-100 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Query History */}
      <div className="card p-4">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="h-5 w-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900">Recent Queries</h2>
        </div>
        {history.length === 0 ? (
          <p className="text-gray-500 text-sm">No query history yet.</p>
        ) : (
          <div className="space-y-2">
            {history.map((h) => (
              <div
                key={h.id}
                className="p-3 rounded-lg border border-gray-100 hover:border-primary-200 cursor-pointer transition-colors"
                onClick={() => { setQueryText(h.query); setResult(null); }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-0.5 text-xs rounded-full ${intentColors[h.intent] || 'bg-gray-100 text-gray-700'}`}>
                    {h.intent.replace('_', ' ')}
                  </span>
                  {h.was_helpful !== null && (
                    <span className={`text-xs ${h.was_helpful ? 'text-green-600' : 'text-red-600'}`}>
                      {h.was_helpful ? '👍' : '👎'}
                    </span>
                  )}
                  {h.timestamp && <span className="text-xs text-gray-400 ml-auto">{new Date(h.timestamp).toLocaleString()}</span>}
                </div>
                <p className="text-sm font-medium text-gray-900">{h.query}</p>
                <p className="text-xs text-gray-500 mt-1 truncate">{h.answer_preview}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
