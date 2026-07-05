'use client'

import { useState } from 'react'
import { Brain, Cpu, CheckCircle, AlertTriangle, XCircle, Settings, Zap } from 'lucide-react'
import { useMultiLLMParse, useLLMProviders, useMultiLLMConfig } from '@/hooks/useNextgenApi'
import type { ConsensusResult } from '@/types/nextgen'

const providerColors: Record<string, string> = {
  github_copilot: 'bg-purple-100 text-purple-700 border-purple-200',
  openai: 'bg-green-100 text-green-700 border-green-200',
  anthropic: 'bg-orange-100 text-orange-700 border-orange-200',
  ollama: 'bg-blue-100 text-blue-700 border-blue-200',
}

const SAMPLE_TEXT = `Under Article 22 of the GDPR, data subjects have the right not to be subject to a decision based solely on automated processing, including profiling, which produces legal effects concerning them. The data controller must implement suitable measures to safeguard the data subject's rights, freedoms, and legitimate interests, at least the right to obtain human intervention, to express their point of view, and to contest the decision.`

export default function MultiLLMDashboard() {
  const [inputText, setInputText] = useState(SAMPLE_TEXT)
  const [result, setResult] = useState<ConsensusResult | null>(null)
  const { data: providers, loading: providersLoading, error: providersError, refetch: refetchProviders } = useLLMProviders()
  const { data: config, loading: configLoading, error: configError, refetch: refetchConfig } = useMultiLLMConfig()
  const { mutate: parse, loading: parsing } = useMultiLLMParse()

  const loading = providersLoading || configLoading
  const error = providersError || configError

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
        </div>
        <div className="card h-32 animate-pulse bg-gray-100" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading Multi-LLM Engine: {error.message}</p>
        <button onClick={() => { refetchProviders(); refetchConfig(); }} className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Retry</button>
      </div>
    )
  }

  const providerList = providers ?? []
  const handleParse = async () => {
    if (!inputText.trim() || parsing) return
    const res = await parse({ text: inputText, strategy: config?.consensus_strategy })
    setResult(res)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Multi-LLM Consensus Engine</h1>
        <p className="text-gray-500">Parse regulatory text with multiple AI models for higher accuracy</p>
      </div>

      {/* Provider Status */}
      {providerList.length === 0 ? (
        <p className="text-gray-500 text-sm">No providers configured.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {providerList.map((p) => (
            <div key={p.provider} className={`card p-4 border ${p.enabled ? providerColors[p.provider] || 'bg-gray-100 text-gray-700 border-gray-200' : 'bg-gray-50 text-gray-400 border-gray-200'}`}>
              <div className="flex items-center justify-between mb-2">
                <Cpu className="h-5 w-5" />
                {p.enabled ? <CheckCircle className="h-4 w-4 text-green-500" /> : <XCircle className="h-4 w-4 text-gray-400" />}
              </div>
              <p className="font-medium text-sm">{p.provider.replace('_', ' ')}</p>
              <p className="text-xs opacity-75">{p.model_name}</p>
              <p className="text-xs mt-1">Weight: {p.weight.toFixed(1)}</p>
            </div>
          ))}
        </div>
      )}

      {/* Config Summary */}
      {config && (
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Settings className="h-5 w-5 text-gray-500" />
            <h2 className="text-lg font-semibold text-gray-900">Configuration</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><span className="text-gray-500">Strategy:</span> <span className="font-medium">{config.consensus_strategy.replace('_', ' ')}</span></div>
            <div><span className="text-gray-500">Min Providers:</span> <span className="font-medium">{config.min_providers}</span></div>
            <div><span className="text-gray-500">Divergence Threshold:</span> <span className="font-medium">{config.divergence_threshold}</span></div>
            <div><span className="text-gray-500">Fallback:</span> <span className="font-medium">{config.fallback_to_single ? 'Enabled' : 'Disabled'}</span></div>
          </div>
        </div>
      )}

      {/* Parse Input */}
      <div className="card p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Regulatory Text Input</h2>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          rows={5}
          className="w-full p-3 rounded-lg border border-gray-200 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 text-sm"
          placeholder="Paste regulatory text to parse..."
        />
        <button
          onClick={handleParse}
          disabled={parsing || !inputText.trim()}
          className="mt-3 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
        >
          {parsing ? <Brain className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
          Parse with Consensus
        </button>
      </div>

      {/* Consensus Result */}
      {result && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="card p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Consensus Result</h2>
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${result.needs_human_review ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                  {result.needs_human_review ? '⚠ Needs Review' : '✓ Consensus Reached'}
                </span>
                <span className="text-sm text-gray-500">{result.total_latency_ms.toFixed(0)}ms</span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">{(result.confidence * 100).toFixed(0)}%</p>
                <p className="text-xs text-gray-500">Confidence</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">{(result.agreement_score * 100).toFixed(0)}%</p>
                <p className="text-xs text-gray-500">Agreement</p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">{result.provider_results.length}</p>
                <p className="text-xs text-gray-500">Providers Used</p>
              </div>
            </div>

            {/* Obligations */}
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Extracted Obligations</h3>
            <div className="space-y-2">
              {result.obligations.map((o, i) => (
                <div key={i} className="flex items-start gap-2 p-2 bg-blue-50 rounded">
                  <span className={`px-1.5 py-0.5 text-xs rounded font-bold ${o.type === 'MUST' ? 'bg-red-200 text-red-800' : 'bg-yellow-200 text-yellow-800'}`}>
                    {String(o.type)}
                  </span>
                  <span className="text-sm text-gray-700">{String(o.text)}</span>
                </div>
              ))}
            </div>

            {/* Entities */}
            <div className="mt-3 flex items-center gap-2">
              <span className="text-sm text-gray-500">Entities:</span>
              {result.entities.map((e) => (
                <span key={e} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">{e}</span>
              ))}
            </div>
          </div>

          {/* Per-Provider Results */}
          <div className="card p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Provider Results</h2>
            <div className="space-y-3">
              {result.provider_results.map((pr) => (
                <div key={pr.provider} className={`p-3 rounded-lg border ${providerColors[pr.provider] || 'border-gray-200'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Cpu className="h-4 w-4" />
                      <span className="font-medium text-sm">{pr.provider.replace('_', ' ')}</span>
                      <span className="text-xs opacity-75">({pr.model_name})</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs">
                      {pr.error ? (
                        <span className="text-red-600 flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> Error</span>
                      ) : (
                        <>
                          <span>Confidence: {(pr.confidence * 100).toFixed(0)}%</span>
                          <span>Latency: {pr.latency_ms.toFixed(0)}ms</span>
                        </>
                      )}
                    </div>
                  </div>
                  {!pr.error && (
                    <div className="text-xs space-y-1">
                      {pr.obligations.map((o, i) => (
                        <p key={i} className="text-gray-600">• {String(o.text || o.type)}</p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* v2: Smart Routing */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🧭 Smart Routing Engine</h2>
        <p className="text-sm text-gray-500 mb-4">Routes parsing requests to optimal providers based on text complexity</p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {[
            { level: 'Simple', route: 'Cheapest provider', color: 'green', example: 'Short definitions' },
            { level: 'Moderate', route: 'Most accurate provider', color: 'blue', example: 'Standard articles' },
            { level: 'Complex', route: 'Consensus of 2+', color: 'orange', example: 'Cross-border rules' },
            { level: 'Critical', route: 'All providers', color: 'red', example: 'Penalties & sanctions' },
          ].map(r => (
            <div key={r.level} className={`p-3 rounded-lg bg-${r.color}-50 border border-${r.color}-200`}>
              <p className={`text-sm font-bold text-${r.color}-900`}>{r.level}</p>
              <p className={`text-xs text-${r.color}-700 mt-1`}>{r.route}</p>
              <p className={`text-xs text-${r.color}-500 mt-2 italic`}>e.g. {r.example}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
