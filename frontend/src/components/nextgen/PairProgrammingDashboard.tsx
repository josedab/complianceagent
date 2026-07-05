'use client'

import { Code2, BookOpen, Lightbulb } from 'lucide-react'
import { usePairProgrammingContext } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function PairProgrammingDashboard() {
  const { data: context, loading, error, refetch } = usePairProgrammingContext('python')

  const ctx = context as Record<string, unknown> | null

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Pair Programming</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{[...Array(3)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Pair Programming</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Pair Programming: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const suggestions = Array.isArray(ctx?.suggestions) ? (ctx.suggestions as Record<string, unknown>[]) : []
  const rules = Array.isArray(ctx?.rules) ? (ctx.rules as Record<string, unknown>[]) : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Pair Programming</h1>
        <p className="text-gray-500">AI-assisted compliance-aware pair programming context</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard icon={<Code2 className="w-5 h-5 text-blue-500" />} title="Language" value={String(ctx?.language ?? 'Python')} subtitle="Active language" />
        <StatCard icon={<Lightbulb className="w-5 h-5 text-yellow-500" />} title="Suggestions" value={String(suggestions.length)} subtitle="Code suggestions" />
        <StatCard icon={<BookOpen className="w-5 h-5 text-green-500" />} title="Rules" value={String(rules.length)} subtitle="Compliance rules" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Suggestions</h2>
          {suggestions.length === 0 ? (
            <p className="text-gray-500">No suggestions available.</p>
          ) : (
            <div className="space-y-3">
              {suggestions.slice(0, 5).map((s, i) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-gray-900">{String(s.title ?? s.type ?? 'Suggestion')}</p>
                      <p className="text-sm text-gray-500 mt-1">{String(s.description ?? s.message ?? '')}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Compliance Rules</h2>
          {rules.length === 0 ? (
            <p className="text-gray-500">No compliance rules loaded.</p>
          ) : (
            <div className="space-y-3">
              {rules.slice(0, 5).map((r, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{String(r.rule_id ?? r.id ?? 'Rule')}</p>
                    <p className="text-sm text-gray-500">{String(r.framework ?? '')} · {String(r.description ?? '')}</p>
                  </div>
                  <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                    {String(r.severity ?? 'info')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
