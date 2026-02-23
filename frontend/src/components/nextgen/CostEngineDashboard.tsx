'use client'

import { DollarSign, Users, TrendingUp, Calculator } from 'lucide-react'

const MOCK_TEAMS = [
  { name: 'Platform Engineering', cost: 12400, frameworks: ['SOC2', 'ISO27001'], repos: 8 },
  { name: 'Payments Team', cost: 8900, frameworks: ['PCI-DSS', 'SOX'], repos: 4 },
  { name: 'Healthcare Division', cost: 15200, frameworks: ['HIPAA', 'SOC2', 'GDPR'], repos: 6 },
  { name: 'Data Science', cost: 5600, frameworks: ['GDPR', 'EU AI Act'], repos: 3 },
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

export default function CostEngineDashboard() {
  const totalCost = MOCK_TEAMS.reduce((s, t) => s + t.cost, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance Cost Engine</h1>
        <p className="text-gray-500">Total cost of compliance ownership and ROI analysis</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<DollarSign className="h-5 w-5 text-blue-600" />} title="Total Cost" value={`$${totalCost.toLocaleString()}/mo`} subtitle="Monthly spend" />
        <StatCard icon={<Users className="h-5 w-5 text-green-600" />} title="Teams" value={String(MOCK_TEAMS.length)} subtitle="Contributing teams" />
        <StatCard icon={<TrendingUp className="h-5 w-5 text-purple-600" />} title="ROI" value="340%" subtitle="Automation savings" />
        <StatCard icon={<Calculator className="h-5 w-5 text-orange-600" />} title="Forecast" value="$486K" subtitle="Annual projected" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Team Cost Breakdown</h2>
        <div className="space-y-3">
          {MOCK_TEAMS.map((team) => (
            <div key={team.name} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{team.name}</span>
                <div className="flex gap-1 mt-1">
                  {team.frameworks.map((f) => (
                    <span key={f} className="px-2 py-0.5 bg-gray-50 text-gray-600 text-xs rounded">{f}</span>
                  ))}
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold text-gray-900">${team.cost.toLocaleString()}</p>
                <p className="text-xs text-gray-500">{team.repos} repos</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
