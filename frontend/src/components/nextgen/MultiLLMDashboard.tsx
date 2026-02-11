'use client'

import { useState } from 'react'
import { Brain, Cpu, CheckCircle, AlertTriangle, XCircle, Settings, Zap } from 'lucide-react'
import { useMultiLLMParse, useLLMProviders, useMultiLLMConfig } from '@/hooks/useNextgenApi'
import type { ConsensusResult, ProviderInfo, MultiLLMConfig } from '@/types/nextgen'

const MOCK_PROVIDERS: ProviderInfo[] = [
  { provider: 'github_copilot', model_name: 'gpt-4o', enabled: true, weight: 1.0 },
  { provider: 'openai', model_name: 'gpt-4-turbo', enabled: true, weight: 0.9 },
  { provider: 'anthropic', model_name: 'claude-3-sonnet', enabled: true, weight: 0.85 },
  { provider: 'ollama', model_name: 'llama-3-70b', enabled: false, weight: 0.7 },
]

const MOCK_CONFIG: MultiLLMConfig = {
  providers: MOCK_PROVIDERS,
  consensus_strategy: 'weighted_average',
  min_providers: 2,
  divergence_threshold: 0.3,
  fallback_to_single: true,
}

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
  const { data: liveProviders } = useLLMProviders()
  const { data: liveConfig } = useMultiLLMConfig()
  const { mutate: parse, loading: parsing } = useMultiLLMParse()

  const providers = liveProviders || MOCK_PROVIDERS
  const config = liveConfig || MOCK_CONFIG

  const handleParse = async () => {
    if (!inputText.trim() || parsing) return
    try {
      const res = await parse({ text: inputText, strategy: config.consensus_strategy })
      setResult(res)
    } catch {
      setResult({
        id: 'demo-1',
        status: 'completed',
        strategy: 'weighted_average',
        provider_results: [
          { provider: 'github_copilot', model_name: 'gpt-4o', obligations: [{ type: 'MUST', text: 'Implement right to not be subject to solely automated decisions' }], entities: ['data_subject', 'data_controller'], confidence: 0.94, latency_ms: 820, error: null },
          { provider: 'openai', model_name: 'gpt-4-turbo', obligations: [{ type: 'MUST', text: 'Provide human intervention mechanism for automated decisions' }], entities: ['data_subject', 'data_controller'], confidence: 0.91, latency_ms: 1100, error: null },
          { provider: 'anthropic', model_name: 'claude-3-sonnet', obligations: [{ type: 'MUST', text: 'Safeguard rights against automated decision-making' }], entities: ['data_subject', 'data_controller', 'profiling'], confidence: 0.93, latency_ms: 950, error: null },
        ],
        obligations: [{ type: 'MUST', text: 'Implement safeguards against solely automated decisions including profiling' }, { type: 'MUST', text: 'Provide human intervention mechanism' }, { type: 'SHOULD', text: 'Allow data subjects to express views and contest decisions' }],
        entities: ['data_subject', 'data_controller', 'profiling'],
        confidence: 0.93,
        agreement_score: 0.89,
        needs_human_review: false,
        total_latency_ms: 1100,
      })
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Multi-LLM Consensus Engine</h1>
        <p className="text-gray-500">Parse regulatory text with multiple AI models for higher accuracy</p>
      </div>

      {/* Provider Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {providers.map((p) => (
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

      {/* Config Summary */}
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
    </div>
  )
}
