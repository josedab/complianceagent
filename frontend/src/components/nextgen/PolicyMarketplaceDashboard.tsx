'use client'

import { useState } from 'react'
import { Package, Star, Download, Search, Code2, FileCode } from 'lucide-react'

interface PolicyPack {
  id: string
  name: string
  description: string
  framework: string
  version: string
  author: string
  downloads: number
  rating: number
  formats: string[]
}

const MOCK_PACKS: PolicyPack[] = [
  { id: 'pp-1', name: 'GDPR Data Protection Bundle', description: 'Complete GDPR compliance policy bundle including consent management, data retention, and breach notification rules.', framework: 'gdpr', version: '2.1.0', author: 'ComplianceAgent', downloads: 2340, rating: 4.8, formats: ['yaml', 'rego', 'python'] },
  { id: 'pp-2', name: 'HIPAA Security Rule Pack', description: 'HIPAA Security Rule compliance policies for PHI protection, access controls, and audit logging.', framework: 'hipaa', version: '1.5.0', author: 'HealthTechOps', downloads: 1856, rating: 4.6, formats: ['yaml', 'rego'] },
  { id: 'pp-3', name: 'PCI-DSS 4.0 Compliance Kit', description: 'Full PCI-DSS 4.0 policy set covering tokenization, encryption, and access control requirements.', framework: 'pci-dss', version: '4.0.1', author: 'SecurePayments', downloads: 3120, rating: 4.9, formats: ['yaml', 'rego', 'python', 'typescript'] },
  { id: 'pp-4', name: 'SOC 2 Type II Controls', description: 'SOC 2 Trust Services Criteria policies for availability, security, and confidentiality.', framework: 'soc2', version: '1.2.0', author: 'AuditReady', downloads: 987, rating: 4.4, formats: ['yaml', 'python'] },
  { id: 'pp-5', name: 'EU AI Act Risk Framework', description: 'AI risk classification and documentation policies aligned with EU AI Act requirements.', framework: 'eu-ai-act', version: '1.0.0', author: 'AIGovernance', downloads: 654, rating: 4.3, formats: ['yaml', 'rego', 'typescript'] },
]

export default function PolicyMarketplaceDashboard() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFormat, setSelectedFormat] = useState<string>('')

  const filteredPacks = MOCK_PACKS.filter(pack => {
    if (searchQuery && !(pack.name + pack.description + pack.framework).toLowerCase().includes(searchQuery.toLowerCase())) return false
    if (selectedFormat && !pack.formats.includes(selectedFormat)) return false
    return true
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Policy Marketplace</h1>
        <p className="text-gray-500 mt-1">Discover, publish, and install compliance-as-code policy bundles</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><Package className="w-4 h-4" /> Total Packs</div>
          <div className="text-2xl font-bold">{MOCK_PACKS.length}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><Download className="w-4 h-4" /> Total Downloads</div>
          <div className="text-2xl font-bold">{MOCK_PACKS.reduce((a, p) => a + p.downloads, 0).toLocaleString()}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><Star className="w-4 h-4" /> Avg Rating</div>
          <div className="text-2xl font-bold">{(MOCK_PACKS.reduce((a, p) => a + p.rating, 0) / MOCK_PACKS.length).toFixed(1)}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border p-4">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-1"><Code2 className="w-4 h-4" /> Formats</div>
          <div className="text-2xl font-bold">4</div>
        </div>
      </div>

      {/* Search + Filter */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
          <input type="text" placeholder="Search policies..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-sm" />
        </div>
        <select value={selectedFormat} onChange={(e) => setSelectedFormat(e.target.value)}
          className="border rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-sm">
          <option value="">All Formats</option>
          <option value="yaml">YAML</option>
          <option value="rego">Rego</option>
          <option value="python">Python</option>
          <option value="typescript">TypeScript</option>
        </select>
      </div>

      {/* Policy Packs */}
      <div className="space-y-3">
        {filteredPacks.map(pack => (
          <div key={pack.id} className="bg-white dark:bg-gray-800 rounded-lg border p-4 hover:border-blue-300 transition-colors">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-medium text-lg">{pack.name}</h3>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">{pack.framework}</span>
                  <span className="text-xs text-gray-400">v{pack.version}</span>
                </div>
                <p className="text-sm text-gray-500 mt-1">{pack.description}</p>
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
                  <span>by {pack.author}</span>
                  <span className="flex items-center gap-1"><Download className="w-3 h-3" />{pack.downloads.toLocaleString()}</span>
                  <span className="flex items-center gap-1"><Star className="w-3 h-3 text-yellow-500" />{pack.rating}</span>
                  <span className="flex items-center gap-1"><FileCode className="w-3 h-3" />{pack.formats.join(', ')}</span>
                </div>
              </div>
              <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors whitespace-nowrap">
                Install
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
