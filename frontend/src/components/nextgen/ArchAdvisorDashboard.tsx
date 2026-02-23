'use client'

import { LayoutDashboard, Shield, Network, FileCode } from 'lucide-react'

const MOCK_DIAGRAMS = [
  { id: 1, name: 'Microservices Event-Driven Architecture', framework: 'React + Node.js', components: 24, format: 'C4 Model', status: 'Validated', lastUpdated: '2024-01-15' },
  { id: 2, name: 'Serverless Data Pipeline', framework: 'AWS Lambda + Python', components: 18, format: 'UML', status: 'Draft', lastUpdated: '2024-01-12' },
  { id: 3, name: 'Multi-Tenant SaaS Platform', framework: 'Next.js + PostgreSQL', components: 32, format: 'ArchiMate', status: 'Validated', lastUpdated: '2024-01-10' },
  { id: 4, name: 'Real-Time Analytics Engine', framework: 'Kafka + Spark', components: 15, format: 'C4 Model', status: 'In Review', lastUpdated: '2024-01-08' },
  { id: 5, name: 'Zero-Trust Security Mesh', framework: 'Istio + Kubernetes', components: 21, format: 'TOGAF', status: 'Validated', lastUpdated: '2024-01-05' },
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

export default function ArchAdvisorDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Architecture Advisor</h1>
        <p className="text-gray-500">Analyze, visualize, and validate software architecture diagrams</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<LayoutDashboard className="w-5 h-5 text-blue-500" />} title="Diagrams" value="5" subtitle="3 validated" />
        <StatCard icon={<Shield className="w-5 h-5 text-green-500" />} title="Frameworks" value="5" subtitle="Across all diagrams" />
        <StatCard icon={<Network className="w-5 h-5 text-purple-500" />} title="Avg Components" value="22" subtitle="Per diagram" />
        <StatCard icon={<FileCode className="w-5 h-5 text-orange-500" />} title="Formats" value="4" subtitle="C4, UML, ArchiMate, TOGAF" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Architecture Diagrams</h2>
        <div className="space-y-3">
          {MOCK_DIAGRAMS.map((diagram) => (
            <div key={diagram.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Network className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="font-medium text-gray-900">{diagram.name}</p>
                  <p className="text-sm text-gray-500">{diagram.framework} · {diagram.components} components · {diagram.format}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  diagram.status === 'Validated' ? 'bg-green-100 text-green-700' :
                  diagram.status === 'Draft' ? 'bg-gray-100 text-gray-700' :
                  'bg-yellow-100 text-yellow-700'
                }`}>
                  {diagram.status}
                </span>
                <span className="text-sm text-gray-400">{diagram.lastUpdated}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
