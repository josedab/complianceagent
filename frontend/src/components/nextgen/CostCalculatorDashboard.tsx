'use client'

import { useState } from 'react'
import { DollarSign, TrendingUp, Clock, Calculator } from 'lucide-react'
import { useCostPrediction, useROICalculation } from '@/hooks/useNextgenApi'
import type { CostPrediction, ROISummary, CostBreakdownItem } from '@/types/nextgen'

const MOCK_PREDICTION: CostPrediction = {
  id: 'pred-001', regulation: 'GDPR', estimated_dev_days: 45, estimated_cost_usd: 67500, confidence: 0.82, risk_score: 6.5,
  breakdown: [
    { phase: 'Assessment', description: 'Gap analysis and requirement mapping', dev_days: 8, cost_usd: 12000 },
    { phase: 'Implementation', description: 'Code changes and new modules', dev_days: 22, cost_usd: 33000 },
    { phase: 'Testing', description: 'Compliance test suite and validation', dev_days: 10, cost_usd: 15000 },
    { phase: 'Documentation', description: 'Policies, procedures, and audit prep', dev_days: 5, cost_usd: 7500 },
  ],
}

const MOCK_ROI: ROISummary = {
  manual_cost_usd: 185000, automated_cost_usd: 67500, savings_usd: 117500, savings_percentage: 63.5, payback_period_months: 2.8, time_saved_days: 78,
}

export default function CostCalculatorDashboard() {
  const [prediction, setPrediction] = useState<CostPrediction>(MOCK_PREDICTION)
  const [roi, setRoi] = useState<ROISummary>(MOCK_ROI)
  const { mutate: predictCost, loading: predicting } = useCostPrediction()
  const { mutate: calcROI, loading: calculatingROI } = useROICalculation()

  const handlePredict = async (regulation: string) => {
    try {
      const result = await predictCost({ regulation })
      setPrediction(result)
      const roiResult = await calcROI({ regulation })
      setRoi(roiResult)
    } catch {
      // Keep mock data on error
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Compliance Cost Calculator</h1>
          <p className="text-gray-500">Predict costs, compare scenarios, and track ROI</p>
        </div>
        <button
          onClick={() => handlePredict(prediction.regulation)}
          disabled={predicting || calculatingROI}
          className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {predicting || calculatingROI ? 'Calculating...' : 'Recalculate'}
        </button>
      </div>

      {/* ROI Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<DollarSign className="h-5 w-5 text-green-600" />} title="Annual Savings" value={`$${(roi.savings_usd).toLocaleString()}`} subtitle={`${roi.savings_percentage}% cost reduction`} />
        <StatCard icon={<Clock className="h-5 w-5 text-blue-600" />} title="Time Saved" value={`${roi.time_saved_days} days`} subtitle="Vs manual compliance" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-purple-600" />} title="Payback Period" value={`${roi.payback_period_months} mo`} subtitle="Time to positive ROI" />
        <StatCard icon={<Calculator className="h-5 w-5 text-orange-600" />} title="Cost Estimate" value={`$${prediction.estimated_cost_usd.toLocaleString()}`} subtitle={`${prediction.estimated_dev_days} dev-days`} />
      </div>

      {/* ROI Comparison */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Manual vs. Automated Compliance</h2>
        <div className="grid grid-cols-2 gap-6">
          <div className="p-4 bg-red-50 rounded-lg border border-red-200">
            <p className="text-sm font-medium text-red-800">Manual Compliance</p>
            <p className="text-3xl font-bold text-red-700 mt-2">${roi.manual_cost_usd.toLocaleString()}</p>
            <p className="text-sm text-red-600 mt-1">{prediction.estimated_dev_days + roi.time_saved_days} dev-days estimated</p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <p className="text-sm font-medium text-green-800">With ComplianceAgent</p>
            <p className="text-3xl font-bold text-green-700 mt-2">${roi.automated_cost_usd.toLocaleString()}</p>
            <p className="text-sm text-green-600 mt-1">{prediction.estimated_dev_days} dev-days estimated</p>
          </div>
        </div>
      </div>

      {/* Cost Breakdown */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost Breakdown — {prediction.regulation}</h2>
        <div className="space-y-3">
          {prediction.breakdown.map((item: CostBreakdownItem, i: number) => {
            const pct = (item.dev_days / prediction.estimated_dev_days) * 100
            return (
              <div key={i} className="p-3 rounded-lg border border-gray-100">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="font-medium text-gray-900">{item.phase}</span>
                    <p className="text-sm text-gray-500">{item.description}</p>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-gray-900">${item.cost_usd.toLocaleString()}</span>
                    <p className="text-sm text-gray-500">{item.dev_days} days</p>
                  </div>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-primary-500 rounded-full" style={{ width: `${pct}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Confidence */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Prediction Confidence</h2>
            <p className="text-sm text-gray-500">Based on historical data and industry benchmarks</p>
          </div>
          <div className="text-right">
            <span className="text-3xl font-bold text-blue-600">{(prediction.confidence * 100).toFixed(0)}%</span>
            <p className="text-sm text-gray-500">Risk Score: {prediction.risk_score}/10</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        {icon}
      </div>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
    </div>
  )
}
