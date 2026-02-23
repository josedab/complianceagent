'use client'

import { Store, Download, Star, Package } from 'lucide-react'

const MOCK_AGENTS = [
  { id: 1, name: 'GDPR Data Mapper', category: 'Privacy', installs: 12400, rating: 4.8, reviews: 234, author: 'ComplianceLabs' },
  { id: 2, name: 'SOC2 Evidence Collector', category: 'Audit', installs: 9800, rating: 4.6, reviews: 187, author: 'AuditTech' },
  { id: 3, name: 'PCI-DSS Scanner Pro', category: 'Security', installs: 15200, rating: 4.9, reviews: 312, author: 'SecureFlow' },
  { id: 4, name: 'HIPAA Risk Assessor', category: 'Healthcare', installs: 7600, rating: 4.5, reviews: 143, author: 'HealthGuard' },
  { id: 5, name: 'ISO 27001 Toolkit', category: 'Standards', installs: 11300, rating: 4.7, reviews: 256, author: 'ISOExperts' },
]

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

export default function AgentsMarketplaceDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Agents Marketplace</h1>
        <p className="text-gray-500">Discover, install, and manage compliance automation agents</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Store className="w-5 h-5 text-blue-500" />} title="Available Agents" value="5" subtitle="Verified and published" />
        <StatCard icon={<Download className="w-5 h-5 text-green-500" />} title="Total Installs" value="56.3K" subtitle="Across all agents" />
        <StatCard icon={<Star className="w-5 h-5 text-yellow-500" />} title="Avg Rating" value="4.7" subtitle="From 1,132 reviews" />
        <StatCard icon={<Package className="w-5 h-5 text-purple-500" />} title="Categories" value="5" subtitle="Privacy, Audit, Security, +" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Marketplace Agents</h2>
        <div className="space-y-3">
          {MOCK_AGENTS.map((agent) => (
            <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Package className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="font-medium text-gray-900">{agent.name}</p>
                  <p className="text-sm text-gray-500">by {agent.author} · {agent.installs.toLocaleString()} installs · {agent.reviews} reviews</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                  {agent.category}
                </span>
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                  <span className="text-sm font-medium text-gray-700">{agent.rating}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
