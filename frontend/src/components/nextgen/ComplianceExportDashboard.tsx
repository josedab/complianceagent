'use client'

import { Download, Calendar, Database, FileSpreadsheet } from 'lucide-react'

const MOCK_EXPORTS = [
  { id: 1, name: 'Q1 2024 SOC2 Report', format: 'PDF', size: '4.2 MB', exportedAt: '2024-03-15', status: 'Completed' },
  { id: 2, name: 'GDPR Data Inventory', format: 'CSV', size: '1.8 MB', exportedAt: '2024-03-14', status: 'Completed' },
  { id: 3, name: 'Monthly Compliance Metrics', format: 'XLSX', size: '920 KB', exportedAt: '2024-03-13', status: 'Processing' },
]

const MOCK_CONNECTORS = [
  { id: 1, name: 'Tableau Cloud', type: 'BI Platform', status: 'Connected', lastSync: '10 min ago' },
  { id: 2, name: 'Power BI', type: 'BI Platform', status: 'Connected', lastSync: '25 min ago' },
  { id: 3, name: 'Snowflake', type: 'Data Warehouse', status: 'Disconnected', lastSync: '2 days ago' },
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

export default function ComplianceExportDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Data Export & BI Integration</h1>
        <p className="text-gray-500">Export compliance data and connect to business intelligence platforms</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Download className="w-5 h-5 text-blue-500" />} title="Total Exports" value="87" subtitle="This month" />
        <StatCard icon={<Calendar className="w-5 h-5 text-green-500" />} title="Scheduled Reports" value="12" subtitle="Auto-generated weekly" />
        <StatCard icon={<Database className="w-5 h-5 text-purple-500" />} title="Connectors" value="3" subtitle="BI integrations configured" />
        <StatCard icon={<FileSpreadsheet className="w-5 h-5 text-yellow-500" />} title="Data Volume" value="6.9 MB" subtitle="Exported this period" />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Exports</h2>
        <div className="space-y-3">
          {MOCK_EXPORTS.map((exp) => (
            <div key={exp.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="font-medium text-gray-900">{exp.name}</p>
                  <p className="text-sm text-gray-500">{exp.format} · {exp.size} · {exp.exportedAt}</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                exp.status === 'Completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              }`}>
                {exp.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">BI Connectors</h2>
        <div className="space-y-3">
          {MOCK_CONNECTORS.map((conn) => (
            <div key={conn.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <Database className="w-5 h-5 text-purple-500" />
                <div>
                  <p className="font-medium text-gray-900">{conn.name}</p>
                  <p className="text-sm text-gray-500">{conn.type} · Last synced {conn.lastSync}</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                conn.status === 'Connected' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
                {conn.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
