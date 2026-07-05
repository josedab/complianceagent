'use client'

import { Shield, CheckCircle, AlertTriangle, Code } from 'lucide-react'
import { useIaCRules } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function IaCPolicyDashboard() {
  const { data: rules, loading, error, refetch } = useIaCRules()

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">IaC Policy Engine</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">IaC Policy Engine</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading IaC Policy Engine: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  const active = rules?.filter(r => r.enabled) ?? []
  const critical = rules?.filter(r => r.severity === 'critical') ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">IaC Policy Engine</h1>
        <p className="text-gray-500">Scan and enforce compliance policies on Infrastructure-as-Code</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Shield className="w-5 h-5 text-blue-500" />} title="Total Rules" value={String(rules?.length ?? 0)} subtitle="Policy rules" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-green-500" />} title="Active" value={String(active.length)} subtitle="Enabled rules" />
        <StatCard icon={<AlertTriangle className="w-5 h-5 text-red-500" />} title="Critical" value={String(critical.length)} subtitle="Critical severity" />
        <StatCard icon={<Code className="w-5 h-5 text-purple-500" />} title="Providers" value={String(rules ? new Set(rules.map(r => r.provider)).size : 0)} subtitle="Cloud providers" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Policy Rules</h2>
        {!rules || rules.length === 0 ? (
          <p className="text-gray-500">No policy rules defined yet.</p>
        ) : (
          <div className="space-y-3">
            {rules.slice(0, 10).map((rule) => (
              <div key={rule.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Shield className={`w-5 h-5 ${rule.severity === 'critical' ? 'text-red-500' : rule.severity === 'high' ? 'text-orange-500' : 'text-yellow-500'}`} />
                  <div>
                    <p className="font-medium text-gray-900">{rule.name}</p>
                    <p className="text-sm text-gray-500">{rule.provider} · {rule.framework}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${rule.severity === 'critical' ? 'bg-red-100 text-red-700' : rule.severity === 'high' ? 'bg-orange-100 text-orange-700' : 'bg-yellow-100 text-yellow-700'}`}>
                    {rule.severity}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${rule.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                    {rule.enabled ? 'Active' : 'Disabled'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
