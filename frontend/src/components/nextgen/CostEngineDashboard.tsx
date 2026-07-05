'use client'

import { DollarSign, TrendingDown, BarChart3, Building } from 'lucide-react'
import { useCostAttributionList, useCostEngineRoi } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function CostEngineDashboard() {
  const { data: attrList, loading: attrLoading, error: attrError, refetch } = useCostAttributionList()
  const { data: roi, loading: roiLoading, error: roiError } = useCostEngineRoi()

  const loading = attrLoading || roiLoading
  const error = attrError || roiError

  const roiData = roi as Record<string, unknown> | null

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Cost Engine</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Cost Engine</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Cost Engine: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const attributions = attrList?.attributions ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Cost Engine</h1>
        <p className="text-gray-500">Track and attribute compliance costs across teams and frameworks</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<DollarSign className="w-5 h-5 text-green-500" />} title="Total Cost" value={`$${(attrList?.total_cost ?? 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`} subtitle="Attributed costs" />
        <StatCard icon={<Building className="w-5 h-5 text-blue-500" />} title="Attributions" value={String(attrList?.total ?? 0)} subtitle="Attribution records" />
        <StatCard icon={<TrendingDown className="w-5 h-5 text-orange-500" />} title="ROI" value={`${((Number(roiData?.roi_percent ?? 0))).toFixed(1)}%`} subtitle="Return on investment" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-purple-500" />} title="Total Hours" value={`${(attrList?.total_hours ?? 0).toFixed(0)}h`} subtitle="Compliance hours" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost Attribution</h2>
        {attributions.length === 0 ? (
          <p className="text-gray-500">No cost attribution data yet.</p>
        ) : (
          <div className="space-y-3">
            {attributions.slice(0, 10).map((attr) => (
              <div key={attr.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <DollarSign className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="font-medium text-gray-900">{attr.team}</p>
                    <p className="text-sm text-gray-500">Framework: {attr.framework} · {attr.hours.toFixed(1)}h</p>
                  </div>
                </div>
                <span className="text-sm font-semibold text-gray-900">${attr.estimated_cost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
