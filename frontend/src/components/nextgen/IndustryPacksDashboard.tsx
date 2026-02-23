'use client'

import { Package, Building2, Shield, Download } from 'lucide-react'

const ITEMS = [
  { id: 1, name: 'Healthcare Pack', detail: 'HIPAA + HITECH controls', value: '156 controls' },
  { id: 2, name: 'Financial Services', detail: 'SOX + PCI DSS bundle', value: '198 controls' },
  { id: 3, name: 'Government Pack', detail: 'FedRAMP + NIST 800-53', value: '234 controls' },
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

export default function IndustryPacksDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Industry Compliance Packs</h1>
        <p className="text-gray-500">Pre-built compliance packages for specific industries</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Package className="h-5 w-5 text-blue-600" />} title="Packs" value="18" subtitle="Available" />
        <StatCard icon={<Building2 className="h-5 w-5 text-green-600" />} title="Controls" value="1.2K" subtitle="Included" />
        <StatCard icon={<Shield className="h-5 w-5 text-purple-600" />} title="Industries" value="8" subtitle="Covered" />
        <StatCard icon={<Download className="h-5 w-5 text-orange-600" />} title="Installs" value="3.4K" subtitle="Total" />
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
