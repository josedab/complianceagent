'use client'

import { Brain, Eye, AlertTriangle, Shield } from 'lucide-react'
import { useAIModels } from '@/hooks/useNextgenApi'
import type { AIModelRecord } from '@/types/nextgen'

interface AIModelDisplay extends AIModelRecord {
  bias_score: number;
  compliant: boolean;
  purpose: string;
  last_audit: string;
}

const MOCK_MODELS: AIModelDisplay[] = [
  { id: 'ai1', name: 'Customer Scoring v3', model_type: 'classifier', version: '3.0', framework: 'pytorch', use_case: 'Credit scoring', risk_level: 'high_risk', status: 'compliant', owner: 'ml-team', bias_score: 0.78, compliant: true, purpose: 'Credit scoring', last_audit: '2026-03-10T10:00:00Z' },
  { id: 'ai2', name: 'Fraud Detection v2', model_type: 'classifier', version: '2.0', framework: 'tensorflow', use_case: 'Transaction monitoring', risk_level: 'high_risk', status: 'compliant', owner: 'security', bias_score: 0.85, compliant: true, purpose: 'Transaction monitoring', last_audit: '2026-03-09T14:00:00Z' },
  { id: 'ai3', name: 'Content Moderation', model_type: 'nlp', version: '1.5', framework: 'transformers', use_case: 'Content filtering', risk_level: 'limited_risk', status: 'non_compliant', owner: 'trust-safety', bias_score: 0.72, compliant: false, purpose: 'User content filtering', last_audit: '2026-03-08T09:00:00Z' },
  { id: 'ai4', name: 'Social Scoring Engine', model_type: 'scoring', version: '1.0', framework: 'sklearn', use_case: 'Social credit assessment', risk_level: 'prohibited', status: 'non_compliant', owner: 'research', bias_score: 0.45, compliant: false, purpose: 'Social credit assessment', last_audit: '2026-03-12T08:00:00Z' },
  { id: 'ai5', name: 'Chatbot Assistant', model_type: 'llm', version: '4.0', framework: 'openai', use_case: 'Customer support', risk_level: 'minimal_risk', status: 'compliant', owner: 'product', bias_score: 0.91, compliant: true, purpose: 'Customer support', last_audit: '2026-03-11T11:00:00Z' },
  { id: 'ai6', name: 'Resume Screener', model_type: 'classifier', version: '2.1', framework: 'pytorch', use_case: 'HR recruitment', risk_level: 'high_risk', status: 'non_compliant', owner: 'hr-tech', bias_score: 0.68, compliant: false, purpose: 'HR recruitment', last_audit: '2026-03-07T15:00:00Z' },
  { id: 'ai7', name: 'Demand Forecaster', model_type: 'regressor', version: '3.2', framework: 'xgboost', use_case: 'Inventory planning', risk_level: 'minimal_risk', status: 'compliant', owner: 'ops', bias_score: 0.94, compliant: true, purpose: 'Inventory planning', last_audit: '2026-03-06T10:00:00Z' },
  { id: 'ai8', name: 'Medical Triage Bot', model_type: 'classifier', version: '1.8', framework: 'pytorch', use_case: 'Patient prioritization', risk_level: 'high_risk', status: 'compliant', owner: 'health', bias_score: 0.81, compliant: true, purpose: 'Patient prioritization', last_audit: '2026-03-05T12:00:00Z' },
]

const riskBadge: Record<string, { bg: string; text: string }> = {
  prohibited: { bg: 'bg-red-100', text: 'text-red-700' },
  high_risk: { bg: 'bg-orange-100', text: 'text-orange-700' },
  limited: { bg: 'bg-yellow-100', text: 'text-yellow-700' },
  minimal: { bg: 'bg-green-100', text: 'text-green-700' },
}

export default function AIObservatoryDashboard() {
  const { data: liveModels } = useAIModels()

  const models = (liveModels as AIModelDisplay[] | null) || MOCK_MODELS
  const highRisk = models.filter(m => m.risk_level === 'high_risk' || m.risk_level === 'prohibited').length
  const compliant = models.filter(m => m.compliant).length
  const avgBias = (models.reduce((sum, m) => sum + m.bias_score, 0) / models.length).toFixed(2)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Model Compliance Observatory</h1>
        <p className="text-gray-500">EU AI Act risk classification, bias monitoring, and MLOps compliance</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Models Tracked</p>
            <Brain className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">{models.length}</p>
          <p className="mt-1 text-sm text-gray-500">In production</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">High-Risk</p>
            <AlertTriangle className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{highRisk}</p>
          <p className="mt-1 text-sm text-gray-500">Require oversight</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Compliant</p>
            <Shield className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{compliant}</p>
          <p className="mt-1 text-sm text-gray-500">Passing all checks</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Avg Bias Score</p>
            <Eye className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">{avgBias}</p>
          <p className="mt-1 text-sm text-gray-500">1.0 = no bias detected</p>
        </div>
      </div>

      {/* Model Cards */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="h-5 w-5 text-purple-500" />
          <h2 className="text-lg font-semibold text-gray-900">AI Models</h2>
        </div>
        <div className="space-y-3">
          {models.map(model => {
            const badge = riskBadge[model.risk_level] || riskBadge.minimal
            return (
              <div key={model.id} className={`p-4 rounded-lg border ${model.compliant ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{model.name}</span>
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${badge.bg} ${badge.text}`}>{model.risk_level.replace('_', ' ')}</span>
                  </div>
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${model.compliant ? 'text-green-700 bg-white' : 'text-red-700 bg-white'}`}>
                    {model.compliant ? 'Compliant' : 'Non-Compliant'}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>{model.purpose}</span>
                  <span>Bias: {model.bias_score}</span>
                  <span>Audited: {new Date(model.last_audit).toLocaleDateString()}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
