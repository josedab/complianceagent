'use client'

import { Network, Search, Database, Eye } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Regulation Network', detail: 'Cross-regulation dependencies', value: '1.2K nodes' },
  { id: 2, name: 'Control Taxonomy', detail: 'Hierarchical control mapping', value: '890 nodes' },
  { id: 3, name: 'Risk Graph', detail: 'Risk relationship explorer', value: '456 nodes' },
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

export default function GraphExplorerDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Knowledge Graph Explorer</h1>
        <p className="text-gray-500">Interactive compliance knowledge graph visualization</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Network className="h-5 w-5 text-blue-600" />} title="Entities" value="3.4K" subtitle="In graph" />
        <StatCard icon={<Search className="h-5 w-5 text-green-600" />} title="Relations" value="12K" subtitle="Mapped" />
        <StatCard icon={<Database className="h-5 w-5 text-purple-600" />} title="Queries" value="567" subtitle="This week" />
        <StatCard icon={<Eye className="h-5 w-5 text-orange-600" />} title="Depth" value="8" subtitle="Max levels" />
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Items</h2>
        <div className="space-y-3">
          {ITEMS.map((item) => (
            <div key={item.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
              <div>
                <span className="font-medium text-gray-900">{item.name}</span>
                <p className="text-xs text-gray-500">{item.detail}</p>
              </div>
              <span className="text-sm text-gray-600">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
