'use client'

import { Cloud, Shield, Server, CheckCircle } from 'lucide-react'
import { useCloudAccounts, useCloudPosture } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">{icon}<span className="text-sm text-gray-500">{title}</span></div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function CrossCloudMeshDashboard() {
  const { data: accounts, loading: accLoading, error: accError, refetch } = useCloudAccounts()
  const { data: posture, loading: posLoading, error: posError } = useCloudPosture()

  const loading = accLoading || posLoading
  const error = accError || posError

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Cross-Cloud Mesh</h1></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">{[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}</div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div><h1 className="text-2xl font-bold text-gray-900">Cross-Cloud Mesh</h1></div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading Cross-Cloud Mesh: {error.message}</p>
          <button onClick={refetch} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Cross-Cloud Compliance Mesh</h1>
        <p className="text-gray-500">Unified compliance posture across AWS, Azure, GCP, and more</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Cloud className="w-5 h-5 text-blue-500" />} title="Cloud Accounts" value={String(accounts?.length ?? 0)} subtitle="Registered accounts" />
        <StatCard icon={<Server className="w-5 h-5 text-green-500" />} title="Total Resources" value={String(posture?.total_resources ?? 0)} subtitle="Discovered resources" />
        <StatCard icon={<Shield className="w-5 h-5 text-purple-500" />} title="Overall Score" value={`${(posture?.overall_score ?? 0).toFixed(1)}%`} subtitle="Posture score" />
        <StatCard icon={<CheckCircle className="w-5 h-5 text-orange-500" />} title="Critical Findings" value={String(posture?.critical_findings ?? 0)} subtitle="Needs attention" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Cloud Accounts</h2>
        {!accounts || accounts.length === 0 ? (
          <p className="text-gray-500">No cloud accounts registered yet.</p>
        ) : (
          <div className="space-y-3">
            {accounts.map((acc) => (
              <div key={acc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Cloud className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{acc.name}</p>
                    <p className="text-sm text-gray-500">{acc.provider} · {acc.account_id} · {acc.resources_discovered} resources</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${acc.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                  {acc.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
