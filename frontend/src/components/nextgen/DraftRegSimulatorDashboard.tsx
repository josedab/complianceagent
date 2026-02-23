'use client'

import { FileSearch, Globe, BarChart3, Zap } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'EU AI Act Draft', detail: 'Impact analysis pending', status: 'Simulating' },
  { id: 2, name: 'SEC Climate Disclosure', detail: 'Financial reporting rules', status: 'Complete' },
  { id: 3, name: 'Digital Services Act', detail: 'Platform compliance', status: 'Complete' },
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

export default function DraftRegSimulatorDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Draft Regulation Simulator</h1>
        <p className="text-gray-500">Simulate and assess impact of upcoming regulations</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<FileSearch className="h-5 w-5 text-blue-600" />} title="Drafts Analyzed" value="19" subtitle="Pending regulations" />
        <StatCard icon={<Globe className="h-5 w-5 text-green-600" />} title="Jurisdictions" value="12" subtitle="Countries covered" />
        <StatCard icon={<BarChart3 className="h-5 w-5 text-purple-600" />} title="Simulations Run" value="87" subtitle="Total this month" />
        <StatCard icon={<Zap className="h-5 w-5 text-orange-600" />} title="Avg Impact Score" value="7.2" subtitle="Out of 10" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Simulations</h2>
        <div className="space-y-3">
          {ITEMS.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail}</p>
              </div>
              <span className="text-sm text-gray-600">{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
