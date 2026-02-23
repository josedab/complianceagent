'use client'

import { useState } from 'react'
import { Key, Package, BarChart3, Code } from 'lucide-react'

interface SDKPackage {
  id: string
  name: string
  version: string
  language: string
  downloads: number
  apiKeys: number
  status: 'stable' | 'beta' | 'deprecated'
}

const statusColors: Record<SDKPackage['status'], string> = {
  stable: 'text-green-700 bg-green-100',
  beta: 'text-blue-700 bg-blue-100',
  deprecated: 'text-red-700 bg-red-100',
}

const MOCK_PACKAGES: SDKPackage[] = [
  { id: 'sdk1', name: '@compliance/policy-engine', version: '2.4.1', language: 'TypeScript', downloads: 12400, apiKeys: 89, status: 'stable' },
  { id: 'sdk2', name: 'compliance-py', version: '1.8.0', language: 'Python', downloads: 8900, apiKeys: 67, status: 'stable' },
  { id: 'sdk3', name: 'compliance-go', version: '0.9.2', language: 'Go', downloads: 3200, apiKeys: 28, status: 'beta' },
]

export default function ComplianceSDKDashboard() {
  const [selectedLang, setSelectedLang] = useState<string>('all')

  const languages = ['all', ...Array.from(new Set(MOCK_PACKAGES.map(p => p.language)))]
  const filtered = selectedLang === 'all'
    ? MOCK_PACKAGES
    : MOCK_PACKAGES.filter(p => p.language === selectedLang)

  const totalDownloads = MOCK_PACKAGES.reduce((a, p) => a + p.downloads, 0)
  const totalKeys = MOCK_PACKAGES.reduce((a, p) => a + p.apiKeys, 0)
  const stableCount = MOCK_PACKAGES.filter(p => p.status === 'stable').length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Code className="h-6 w-6 text-indigo-600" />
          Compliance-as-Code SDK
        </h1>
        <p className="text-gray-500">Developer tools for programmatic compliance management</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">SDK Packages</p>
            <Package className="h-5 w-5 text-indigo-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-indigo-600">{MOCK_PACKAGES.length}</p>
          <p className="mt-1 text-sm text-gray-500">{stableCount} stable</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Total Downloads</p>
            <BarChart3 className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-blue-600">{(totalDownloads / 1000).toFixed(1)}K</p>
          <p className="mt-1 text-sm text-gray-500">All-time installs</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">API Keys</p>
            <Key className="h-5 w-5 text-green-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-green-600">{totalKeys}</p>
          <p className="mt-1 text-sm text-gray-500">Active keys</p>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-gray-500">Languages</p>
            <Code className="h-5 w-5 text-orange-600" />
          </div>
          <p className="mt-2 text-3xl font-bold text-orange-600">{languages.length - 1}</p>
          <p className="mt-1 text-sm text-gray-500">Supported</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {languages.map(l => (
          <button
            key={l}
            onClick={() => setSelectedLang(l)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium ${
              selectedLang === l ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {l === 'all' ? 'All Languages' : l}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {filtered.map(pkg => (
          <div key={pkg.id} className="card">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${statusColors[pkg.status]}`}>
                    {pkg.status.charAt(0).toUpperCase() + pkg.status.slice(1)}
                  </span>
                  <span className="text-xs text-gray-500">v{pkg.version} &middot; {pkg.language}</span>
                </div>
                <h3 className="font-semibold text-gray-900 font-mono">{pkg.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{pkg.apiKeys} API keys &middot; {pkg.downloads.toLocaleString()} downloads</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">{(pkg.downloads / 1000).toFixed(1)}K</p>
                <p className="text-xs text-gray-500">downloads</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
