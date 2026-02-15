'use client'

import { useState } from 'react'
import { Server, Shield, HardDrive, Activity, Download, Key, Settings, CheckCircle, AlertTriangle, Cpu } from 'lucide-react'

type LicenseType = 'trial' | 'standard' | 'enterprise' | 'government'

interface License {
  id: string
  license_key: string
  license_type: LicenseType
  status: string
  organization: string
  max_users: number
  max_repositories: number
  features: string[]
  is_valid: boolean
  expires_at: string | null
}

interface OfflineBundle {
  id: string
  name: string
  version: string
  frameworks: string[]
  regulation_count: number
  size_mb: number
}

interface SystemHealth {
  status: string
  version: string
  uptime_seconds: number
  database_connected: boolean
  llm_available: boolean
  license_valid: boolean
  disk_usage_percent: number
  memory_usage_percent: number
}

const MOCK_LICENSE: License = {
  id: 'lic-001', license_key: 'CA-ENTERPRISE-A1B2C3D4E5F6', license_type: 'enterprise',
  status: 'active', organization: 'Acme Corp', max_users: 100, max_repositories: 50,
  features: ['core_scanning', 'reporting', 'api_access', 'all_frameworks', 'ci_cd', 'sso', 'audit_portal', 'custom_policies', 'priority_support'],
  is_valid: true, expires_at: '2027-02-14T00:00:00Z',
}

const MOCK_HEALTH: SystemHealth = {
  status: 'healthy', version: '3.0.0', uptime_seconds: 864000,
  database_connected: true, llm_available: true, license_valid: true,
  disk_usage_percent: 35.0, memory_usage_percent: 42.0,
}

const MOCK_BUNDLES: OfflineBundle[] = [
  { id: 'b1', name: 'Core Regulations Bundle', version: '2026.1', frameworks: ['gdpr', 'hipaa', 'pci_dss', 'soc2'], regulation_count: 45, size_mb: 128.5 },
  { id: 'b2', name: 'EU Regulations Bundle', version: '2026.1', frameworks: ['gdpr', 'eu_ai_act', 'dora', 'nis2'], regulation_count: 30, size_mb: 95.2 },
  { id: 'b3', name: 'US Healthcare Bundle', version: '2026.1', frameworks: ['hipaa', 'hitech'], regulation_count: 18, size_mb: 42.0 },
  { id: 'b4', name: 'Financial Services Bundle', version: '2026.1', frameworks: ['pci_dss', 'sox', 'dora', 'glba'], regulation_count: 35, size_mb: 88.7 },
]

const MOCK_K8S_RESOURCES = {
  small: { cpu: '2 cores', memory: '4 Gi', storage: '50 Gi', nodes: 2, estimated_cost: '$150/mo' },
  medium: { cpu: '4 cores', memory: '8 Gi', storage: '100 Gi', nodes: 3, estimated_cost: '$400/mo' },
  large: { cpu: '8 cores', memory: '16 Gi', storage: '250 Gi', nodes: 5, estimated_cost: '$900/mo' },
}

const MOCK_IMAGES = [
  { name: 'ghcr.io/complianceagent/server', tag: '3.0.0', size: '245 MB' },
  { name: 'ghcr.io/complianceagent/worker', tag: '3.0.0', size: '210 MB' },
  { name: 'ghcr.io/complianceagent/frontend', tag: '3.0.0', size: '85 MB' },
  { name: 'postgres', tag: '16-alpine', size: '115 MB' },
  { name: 'redis', tag: '7-alpine', size: '30 MB' },
  { name: 'elasticsearch', tag: '8.12.0', size: '850 MB' },
]

const licenseColors: Record<string, { bg: string; text: string }> = {
  trial: { bg: 'bg-gray-100', text: 'text-gray-700' },
  standard: { bg: 'bg-blue-100', text: 'text-blue-700' },
  enterprise: { bg: 'bg-purple-100', text: 'text-purple-700' },
  government: { bg: 'bg-green-100', text: 'text-green-700' },
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  return `${d}d ${h}h`
}

export default function SelfHostedDashboard() {
  const [activeTab, setActiveTab] = useState<'overview' | 'license' | 'bundles' | 'k8s'>('overview')
  const [selectedSize, setSelectedSize] = useState<'small' | 'medium' | 'large'>('medium')

  const license = MOCK_LICENSE
  const health = MOCK_HEALTH
  const bundles = MOCK_BUNDLES
  const lc = licenseColors[license.license_type] || licenseColors.trial

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: Activity },
    { id: 'license' as const, label: 'License', icon: Key },
    { id: 'bundles' as const, label: 'Offline Bundles', icon: Download },
    { id: 'k8s' as const, label: 'Kubernetes', icon: Cpu },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Self-Hosted Deployment</h1>
        <p className="text-gray-500">Manage on-premise and air-gapped deployments</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium ${
                activeTab === id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Health Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-500">System Status</p>
                {health.status === 'healthy' ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-yellow-600" />
                )}
              </div>
              <p className={`mt-2 text-3xl font-bold ${health.status === 'healthy' ? 'text-green-600' : 'text-yellow-600'}`}>
                {health.status}
              </p>
              <p className="mt-1 text-sm text-gray-500">v{health.version}</p>
            </div>
            <div className="card">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-500">Uptime</p>
                <Server className="h-5 w-5 text-blue-600" />
              </div>
              <p className="mt-2 text-3xl font-bold text-gray-900">{formatUptime(health.uptime_seconds)}</p>
              <p className="mt-1 text-sm text-gray-500">Since last restart</p>
            </div>
            <div className="card">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-500">Disk Usage</p>
                <HardDrive className="h-5 w-5 text-indigo-600" />
              </div>
              <p className="mt-2 text-3xl font-bold text-gray-900">{health.disk_usage_percent}%</p>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div className="bg-indigo-600 h-2 rounded-full" style={{ width: `${health.disk_usage_percent}%` }} />
              </div>
            </div>
            <div className="card">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-500">Memory</p>
                <Cpu className="h-5 w-5 text-orange-600" />
              </div>
              <p className="mt-2 text-3xl font-bold text-gray-900">{health.memory_usage_percent}%</p>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div className="bg-orange-500 h-2 rounded-full" style={{ width: `${health.memory_usage_percent}%` }} />
              </div>
            </div>
          </div>

          {/* Services */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Service Status</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { name: 'Database', connected: health.database_connected },
                { name: 'LLM Engine', connected: health.llm_available },
                { name: 'License', connected: health.license_valid },
                { name: 'Redis Cache', connected: true },
              ].map(svc => (
                <div key={svc.name} className={`p-3 rounded-lg border ${svc.connected ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                  <div className="flex items-center gap-2">
                    <div className={`h-2.5 w-2.5 rounded-full ${svc.connected ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-sm font-medium text-gray-700">{svc.name}</span>
                  </div>
                  <p className={`mt-1 text-xs ${svc.connected ? 'text-green-600' : 'text-red-600'}`}>
                    {svc.connected ? 'Connected' : 'Disconnected'}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {activeTab === 'license' && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Active License</h2>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${lc.bg} ${lc.text}`}>
                {license.license_type}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Organization</p>
                <p className="font-medium text-gray-900">{license.organization}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">License Key</p>
                <p className="font-mono text-sm text-gray-900">{license.license_key.slice(0, 20)}...</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Max Users</p>
                <p className="font-medium text-gray-900">{license.max_users}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Max Repositories</p>
                <p className="font-medium text-gray-900">{license.max_repositories}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Status</p>
                <span className={`inline-flex items-center gap-1 ${license.is_valid ? 'text-green-600' : 'text-red-600'}`}>
                  {license.is_valid ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                  {license.is_valid ? 'Valid' : 'Invalid'}
                </span>
              </div>
              <div>
                <p className="text-sm text-gray-500">Expires</p>
                <p className="font-medium text-gray-900">
                  {license.expires_at ? new Date(license.expires_at).toLocaleDateString() : 'Never'}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <h3 className="text-md font-semibold text-gray-900 mb-3">Licensed Features</h3>
            <div className="flex flex-wrap gap-2">
              {license.features.map(f => (
                <span key={f} className="px-2 py-1 bg-indigo-50 text-indigo-700 text-xs rounded-full font-medium">
                  {f.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'bundles' && (
        <div className="space-y-4">
          {bundles.map(bundle => (
            <div key={bundle.id} className="card">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{bundle.name}</h3>
                  <p className="text-sm text-gray-500">v{bundle.version} · {bundle.regulation_count} regulations · {bundle.size_mb} MB</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700">
                  <Download className="h-4 w-4" />
                  Download
                </button>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {bundle.frameworks.map(fw => (
                  <span key={fw} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                    {fw.toUpperCase()}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'k8s' && (
        <div className="space-y-6">
          {/* Resource Calculator */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Settings className="h-5 w-5 text-indigo-600" />
              <h2 className="text-lg font-semibold text-gray-900">Kubernetes Resource Calculator</h2>
            </div>
            <div className="flex gap-3 mb-4">
              {(['small', 'medium', 'large'] as const).map(size => (
                <button
                  key={size}
                  onClick={() => setSelectedSize(size)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium border ${
                    selectedSize === size
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {size.charAt(0).toUpperCase() + size.slice(1)} ({size === 'small' ? '<50 users' : size === 'medium' ? '50-200 users' : '200+ users'})
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(MOCK_K8S_RESOURCES[selectedSize]).map(([key, value]) => (
                <div key={key} className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 uppercase">{key.replace('_', ' ')}</p>
                  <p className="text-lg font-bold text-gray-900">{value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Air-Gapped Images */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="h-5 w-5 text-green-600" />
              <h2 className="text-lg font-semibold text-gray-900">Air-Gapped Container Images</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-gray-500 font-medium">Image</th>
                    <th className="text-left py-2 text-gray-500 font-medium">Tag</th>
                    <th className="text-left py-2 text-gray-500 font-medium">Size</th>
                    <th className="text-right py-2 text-gray-500 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {MOCK_IMAGES.map(img => (
                    <tr key={img.name} className="border-b border-gray-100">
                      <td className="py-3 font-mono text-gray-900">{img.name}</td>
                      <td className="py-3 text-gray-600">{img.tag}</td>
                      <td className="py-3 text-gray-600">{img.size}</td>
                      <td className="py-3 text-right">
                        <button className="text-indigo-600 hover:text-indigo-800 text-sm font-medium">Pull</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-sm text-gray-500">
              Total image size: {MOCK_IMAGES.reduce((acc, img) => acc + parseFloat(img.size), 0).toFixed(0)} MB
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
