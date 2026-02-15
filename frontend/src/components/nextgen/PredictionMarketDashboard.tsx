'use client'

import { useState } from 'react'
import { TrendingUp, Users } from 'lucide-react'

interface Market {
  id: string
  title: string
  description: string
  regulation: string
  jurisdiction: string
  currentProbability: number
  totalVolume: number
  totalParticipants: number
  resolutionCriteria: string
  closesAt: string
}

interface Forecaster {
  displayName: string
  totalPredictions: number
  correctPredictions: number
  brierScore: number
  accuracyRate: number
  totalPnl: number
  rank: number
  isSuperforecaster: boolean
}

const MOCK_MARKETS: Market[] = [
  { id: '1', title: 'EU AI Act Enforcement by Feb 2026', description: 'Will the EU AI Act be fully enforceable by February 2, 2026?',
    regulation: 'EU AI Act', jurisdiction: 'EU', currentProbability: 0.72, totalVolume: 15400, totalParticipants: 89,
    resolutionCriteria: 'Official EU gazette publication', closesAt: new Date(Date.now() + 180 * 86400000).toISOString() },
  { id: '2', title: 'US Federal Privacy Law by 2025', description: 'Will the US pass a comprehensive federal privacy law by end of 2025?',
    regulation: 'ADPPA', jurisdiction: 'US', currentProbability: 0.18, totalVolume: 8900, totalParticipants: 67,
    resolutionCriteria: 'Bill signed into law', closesAt: new Date(Date.now() + 120 * 86400000).toISOString() },
  { id: '3', title: 'GDPR Fine >€100M in 2025', description: 'Will any single GDPR fine exceed €100 million in 2025?',
    regulation: 'GDPR', jurisdiction: 'EU', currentProbability: 0.45, totalVolume: 12300, totalParticipants: 112,
    resolutionCriteria: 'Official DPA announcement', closesAt: new Date(Date.now() + 200 * 86400000).toISOString() },
  { id: '4', title: 'California AI Transparency Law', description: 'Will California enact AI transparency requirements by 2026?',
    regulation: 'CA AI Act', jurisdiction: 'US-CA', currentProbability: 0.63, totalVolume: 5600, totalParticipants: 41,
    resolutionCriteria: 'Governor signature', closesAt: new Date(Date.now() + 300 * 86400000).toISOString() },
]

const MOCK_FORECASTERS: Forecaster[] = [
  { displayName: 'RegOracle', totalPredictions: 45, correctPredictions: 38, brierScore: 0.12, accuracyRate: 0.844, totalPnl: 2340, rank: 1, isSuperforecaster: true },
  { displayName: 'PolicyPredictor', totalPredictions: 38, correctPredictions: 30, brierScore: 0.18, accuracyRate: 0.789, totalPnl: 1560, rank: 2, isSuperforecaster: true },
  { displayName: 'ComplianceSeer', totalPredictions: 52, correctPredictions: 39, brierScore: 0.21, accuracyRate: 0.75, totalPnl: 980, rank: 3, isSuperforecaster: false },
  { displayName: 'GRCGuru', totalPredictions: 28, correctPredictions: 20, brierScore: 0.25, accuracyRate: 0.714, totalPnl: 450, rank: 4, isSuperforecaster: false },
]

const probColor = (p: number) => p >= 0.7 ? 'text-green-600' : p >= 0.4 ? 'text-yellow-600' : 'text-red-600'

export default function PredictionMarketDashboard() {
  const [activeTab, setActiveTab] = useState<'markets' | 'forecasters'>('markets')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><TrendingUp className="h-7 w-7 text-violet-600" /> Prediction Market</h1>
        <p className="text-gray-500 mt-1">Forecast regulatory outcomes with collective intelligence</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Active Markets</div>
          <div className="text-2xl font-bold">{MOCK_MARKETS.length}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Total Volume</div>
          <div className="text-2xl font-bold">${(MOCK_MARKETS.reduce((s, m) => s + m.totalVolume, 0) / 1000).toFixed(1)}K</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Participants</div>
          <div className="text-2xl font-bold">{MOCK_MARKETS.reduce((s, m) => s + m.totalParticipants, 0)}</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-sm text-gray-500">Forecast Accuracy</div>
          <div className="text-2xl font-bold text-green-600">78%</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        <button onClick={() => setActiveTab('markets')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium ${activeTab === 'markets' ? 'bg-white shadow text-violet-600' : 'text-gray-600'}`}>
          📈 Markets
        </button>
        <button onClick={() => setActiveTab('forecasters')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium ${activeTab === 'forecasters' ? 'bg-white shadow text-violet-600' : 'text-gray-600'}`}>
          🏆 Top Forecasters
        </button>
      </div>

      {activeTab === 'markets' && (
        <div className="space-y-4">
          {MOCK_MARKETS.map(market => {
            const daysLeft = Math.ceil((new Date(market.closesAt).getTime() - Date.now()) / 86400000)
            return (
              <div key={market.id} className="bg-white rounded-lg border p-5 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="bg-violet-50 text-violet-700 text-xs px-2 py-0.5 rounded">{market.regulation}</span>
                      <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded">{market.jurisdiction}</span>
                    </div>
                    <h3 className="text-lg font-semibold">{market.title}</h3>
                    <p className="text-gray-600 text-sm mt-1">{market.description}</p>
                  </div>
                  <div className="text-right ml-4">
                    <div className={`text-3xl font-bold ${probColor(market.currentProbability)}`}>
                      {(market.currentProbability * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500">probability</div>
                  </div>
                </div>
                {/* Probability Bar */}
                <div className="mt-3">
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${market.currentProbability >= 0.5 ? 'bg-green-500' : 'bg-red-500'}`}
                      style={{ width: `${market.currentProbability * 100}%` }} />
                  </div>
                </div>
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                  <span><Users className="h-3 w-3 inline" /> {market.totalParticipants}</span>
                  <span>${market.totalVolume.toLocaleString()} volume</span>
                  <span>{daysLeft}d remaining</span>
                </div>
                <div className="mt-3 flex gap-2">
                  <button className="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700">Buy Yes</button>
                  <button className="px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700">Buy No</button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {activeTab === 'forecasters' && (
        <div className="bg-white rounded-lg border">
          <div className="divide-y">
            {MOCK_FORECASTERS.map(f => (
              <div key={f.rank} className="p-4 flex items-center gap-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${f.rank <= 2 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'}`}>
                  {f.rank}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{f.displayName}</span>
                    {f.isSuperforecaster && <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">⭐ Superforecaster</span>}
                  </div>
                  <div className="text-sm text-gray-500">{f.correctPredictions}/{f.totalPredictions} correct · Brier: {f.brierScore.toFixed(2)}</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-green-600">{(f.accuracyRate * 100).toFixed(1)}%</div>
                  <div className="text-xs text-gray-500">+${f.totalPnl.toLocaleString()}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
