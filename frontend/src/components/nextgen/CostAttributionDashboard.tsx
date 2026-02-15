'use client'

import { DollarSign, PieChart, TrendingDown, Calculator } from 'lucide-react'
import { useCostDashboard } from '@/hooks/useNextgenApi'

const MOCK_BREAKDOWN = [
  { id: 'cb1', regulation: 'GDPR', total_cost: 450000, categories: { tooling: 180000, personnel: 200000, training: 40000, audit: 30000 }, mom_change: -8 },
  { id: 'cb2', regulation: 'SOC 2', total_cost: 320000, categories: { tooling: 120000, personnel: 150000, training: 25000, audit: 25000 }, mom_change: -15 },
  { id: 'cb3', regulation: 'HIPAA', total_cost: 210000, categories: { tooling: 80000, personnel: 90000, training: 20000, audit: 20000 }, mom_change: -5 },
  { id: 'cb4', regulation: 'PCI DSS', total_cost: 150000, categories: { tooling: 60000, personnel: 60000, training: 15000, audit: 15000 }, mom_change: -18 },
  { id: 'cb5', regulation: 'ISO 27001', total_cost: 70000, categories: { tooling: 25000, personnel: 30000, training: 10000, audit: 5000 }, mom_change: -22 },
]

const categoryColors: Record<string, string> = {
  tooling: 'bg-blue-500',
  personnel: 'bg-purple-500',
  training: 'bg-green-500',
  audit: 'bg-orange-500',
}

export default function CostAttributionDashboard() {
  const { data: liveDashboard } = useCostDashboard()

  const breakdown = liveDashboard ? [] : MOCK_BREAKDOWN
  const totalCost = breakdown.reduce((sum, b) => sum + b.total_cost, 0)
  const topReg = breakdown.length > 0 ? breakdown.sort((a, b) => b.total_cost - a.total_cost)[0] : null
  const avgChange = (breakdown.reduce((sum, b) => sum + b.mom_change, 0) / breakdown.length).toFixed(0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Cost Attribution Engine</h1>
        <p className="text-gray-500">Attribute compliance costs to regulations and code modules</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Total Cost</p>
            <DollarSign className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-gray-900">${(totalCost / 1000000).toFixed(1)}M</p>
          <p className="mt-1 text-sm text-gray-500">Annual compliance spend</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Top Regulation</p>
            <PieChart className="h-5 w-5 text-purple-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-purple-600">{topReg?.regulation || 'GDPR'}</p>
          <p className="mt-1 text-sm text-gray-500">${topReg ? (topReg.total_cost / 1000).toFixed(0) : '450'}K</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">ROI</p>
            <Calculator className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">340%</p>
          <p className="mt-1 text-sm text-gray-500">Return on investment</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">MoM Change</p>
            <TrendingDown className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{avgChange}%</p>
          <p className="mt-1 text-sm text-green-500">Cost reduction</p>
        </div>
      </div>

      {/* Cost Breakdown */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <PieChart className="h-5 w-5 text-purple-500" />
          <h2 className="text-lg font-semibold text-gray-900">Cost Breakdown by Regulation</h2>
        </div>
        <div className="space-y-4">
          {breakdown.map(item => (
            <div key={item.id} className="p-4 rounded-lg border border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900">{item.regulation}</span>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-gray-900">${(item.total_cost / 1000).toFixed(0)}K</span>
                  <span className={`text-sm ${item.mom_change < 0 ? 'text-green-600' : 'text-red-600'}`}>{item.mom_change}%</span>
                </div>
              </div>
              <div className="flex h-3 rounded-full overflow-hidden">
                {Object.entries(item.categories).map(([cat, val]) => (
                  <div key={cat} className={`${categoryColors[cat]}`} style={{ width: `${(val / item.total_cost) * 100}%` }} title={`${cat}: $${(val / 1000).toFixed(0)}K`} />
                ))}
              </div>
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                {Object.entries(item.categories).map(([cat, val]) => (
                  <span key={cat} className="flex items-center gap-1">
                    <span className={`inline-block w-2 h-2 rounded-full ${categoryColors[cat]}`} />{cat}: ${(val / 1000).toFixed(0)}K
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
