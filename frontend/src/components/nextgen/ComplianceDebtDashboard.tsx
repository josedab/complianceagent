'use client'

import { AlertTriangle, DollarSign, CheckCircle, BarChart3 } from 'lucide-react'
import { useComplianceDebtItems, useComplianceDebtStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function ComplianceDebtDashboard() {
  const { data: items, loading: itemsLoading, error: itemsError, refetch } = useComplianceDebtItems()
  const { data: stats, loading: statsLoading, error: statsError } = useComplianceDebtStats()

  const loading = itemsLoading || statsLoading
  const error = itemsError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Debt</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Compliance Debt</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Compliance Debt: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Debt</h1>
        <p className="text-gray-500">Track and prioritize compliance gaps across repositories</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-orange-500" />} title="Open Items" value={String(stats?.open_items ?? 0)} subtitle="Unresolved gaps" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-500" />} title="Resolved" value={String(stats?.resolved_items ?? 0)} subtitle="Fixed items" />
        <StatCard icon={<DollarSign className="w-5 h-5 text-red-500" />} title="Risk Cost" value={`$${(stats?.total_risk_cost_usd ?? 0).toLocaleString(undefined, {maximumFractionDigits: 0})}`} subtitle="Estimated risk" />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-blue-500" />} title="Remediation Cost" value={`$${(stats?.total_remediation_cost_usd ?? 0).toLocaleString(undefined, {maximumFractionDigits: 0})}`} subtitle="To fix" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Debt Items</h2>
        {!items || items.length === 0 ? (
          <p className="text-gray-500">No compliance debt items yet.</p>
        ) : (
          <div className="space-y-3">
            {items.slice(0, 10).map((item) => (
              <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <AlertTriangle className={`w-5 h-5 ${item.severity === 'critical' ? 'text-red-500' : item.severity === 'high' ? 'text-orange-500' : 'text-yellow-500'}`} />
                  <div>
                    <p className="font-medium text-gray-900">{item.title}</p>
                    <p className="text-sm text-gray-500">{item.repo} · {item.framework} · Risk: ${item.risk_cost_usd.toFixed(0)}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  item.severity === 'critical' ? 'bg-red-100 text-red-700' :
                  item.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                  'bg-yellow-100 text-yellow-700'
                }`}>{item.severity}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
