'use client'

import { Key, Globe, BarChart3, Shield } from 'lucide-react'
import { useGatewayClients, useGatewayStats } from '@/hooks/useNextgenApi'

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm text-gray-500">{title}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
    </div>
  )
}

export default function APIGatewayDashboard() {
  const { data: clients, loading: clientsLoading, error: clientsError, refetch: refetchClients } = useGatewayClients()
  const { data: stats, loading: statsLoading, error: statsError } = useGatewayStats()

  const loading = clientsLoading || statsLoading
  const error = clientsError || statsError

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Gateway</h1>
          <p className="text-gray-500">Manage OAuth clients, rate limiting, and API traffic</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <div key={i} className="card h-24 bg-gray-100 animate-pulse" />)}
        </div>
        <div className="card h-48 bg-gray-100 animate-pulse" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Gateway</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading API Gateway: {error.message}</p>
          <button onClick={refetchClients} className="mt-2 text-sm text-red-600 underline">Retry</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">API Gateway</h1>
        <p className="text-gray-500">Manage OAuth clients, rate limiting, and API traffic</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Key className="w-5 h-5 text-blue-500" />} title="OAuth Clients" value={String(stats?.total_clients ?? 0)} subtitle={`${stats?.active_clients ?? 0} active`} />
        <StatCard icon={<Globe className="w-5 h-5 text-green-500" />} title="Total Requests" value={String(stats?.total_requests ?? 0)} subtitle={`${stats?.requests_today ?? 0} today`} />
        <StatCard icon={<BarChart3 className="w-5 h-5 text-purple-500" />} title="Rate Limited" value={String(stats?.rate_limited_count ?? 0)} subtitle="Rate limit hits" />
        <StatCard icon={<Shield className="w-5 h-5 text-orange-500" />} title="Active Clients" value={String(stats?.active_clients ?? 0)} subtitle={`of ${stats?.total_clients ?? 0} total`} />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">OAuth Clients</h2>
        {!clients || clients.length === 0 ? (
          <p className="text-gray-500">No clients registered yet.</p>
        ) : (
          <div className="space-y-3">
            {clients.map((client) => (
              <div key={client.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Key className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="font-medium text-gray-900">{client.name}</p>
                    <p className="text-sm text-gray-500">{client.scopes.join(', ')} · {client.rate_limit_per_minute} req/min</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${client.active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {client.active ? 'Active' : 'Inactive'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
