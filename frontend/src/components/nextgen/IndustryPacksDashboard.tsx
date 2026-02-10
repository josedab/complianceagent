'use client'

import { Package, Rocket, CheckCircle, Zap } from 'lucide-react'
import { useIndustryPacks, useProvisionPack } from '@/hooks/useNextgenApi'
import type { IndustryPack } from '@/types/nextgen'

const MOCK_PACKS: IndustryPack[] = [
  {
    name: 'Fintech Compliance Pack', vertical: 'fintech', description: 'Complete compliance suite for financial services',
    regulations: [
      { regulation: 'GDPR', description: 'General Data Protection Regulation', priority: 'critical' },
      { regulation: 'PCI-DSS', description: 'Payment Card Industry Data Security', priority: 'critical' },
      { regulation: 'SOX', description: 'Sarbanes-Oxley Act', priority: 'high' },
      { regulation: 'AML/KYC', description: 'Anti-Money Laundering regulations', priority: 'high' },
    ],
    policy_templates: [
      { name: 'Data Protection Policy', description: 'GDPR-compliant data protection policy', category: 'privacy' },
      { name: 'PCI-DSS Security Policy', description: 'Card data handling procedures', category: 'security' },
    ],
    status: 'available',
  },
  {
    name: 'Healthtech Compliance Pack', vertical: 'healthtech', description: 'HIPAA and healthcare regulatory compliance',
    regulations: [
      { regulation: 'HIPAA', description: 'Health Insurance Portability and Accountability', priority: 'critical' },
      { regulation: 'GDPR', description: 'For EU patient data', priority: 'high' },
      { regulation: 'FDA 21 CFR Part 11', description: 'Electronic records and signatures', priority: 'medium' },
    ],
    policy_templates: [
      { name: 'HIPAA Privacy Policy', description: 'PHI handling and privacy procedures', category: 'privacy' },
      { name: 'Breach Response Plan', description: '60-day breach notification procedures', category: 'incident' },
    ],
    status: 'provisioned',
  },
  {
    name: 'AI Company Compliance Pack', vertical: 'ai_company', description: 'EU AI Act and AI governance compliance',
    regulations: [
      { regulation: 'EU AI Act', description: 'European AI regulation', priority: 'critical' },
      { regulation: 'NIST AI RMF', description: 'AI Risk Management Framework', priority: 'high' },
      { regulation: 'ISO 42001', description: 'AI Management System standard', priority: 'medium' },
    ],
    policy_templates: [
      { name: 'AI Ethics Policy', description: 'Responsible AI development guidelines', category: 'governance' },
      { name: 'Model Risk Management', description: 'AI model lifecycle governance', category: 'risk' },
    ],
    status: 'available',
  },
  {
    name: 'E-Commerce Compliance Pack', vertical: 'ecommerce', description: 'Consumer privacy and payment compliance',
    regulations: [
      { regulation: 'GDPR', description: 'EU customer data protection', priority: 'critical' },
      { regulation: 'CCPA', description: 'California consumer privacy', priority: 'high' },
      { regulation: 'PCI-DSS', description: 'Payment processing security', priority: 'critical' },
    ],
    policy_templates: [
      { name: 'Cookie Consent Policy', description: 'EU cookie directive compliance', category: 'privacy' },
    ],
    status: 'available',
  },
]

const statusColors = { available: 'bg-blue-100 text-blue-700', provisioned: 'bg-green-100 text-green-700', active: 'bg-green-100 text-green-700' }
const priorityColors = { critical: 'text-red-600', high: 'text-orange-600', medium: 'text-yellow-600', low: 'text-gray-600' }

export default function IndustryPacksDashboard() {
  const { data: livePacks, refetch } = useIndustryPacks()
  const { mutate: provisionPack, loading: provisioning } = useProvisionPack()

  const packs = livePacks || MOCK_PACKS

  const handleProvision = async (vertical: string) => {
    try {
      await provisionPack(vertical)
      refetch()
    } catch {
      // Keep current state on error
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Industry Compliance Packs</h1>
        <p className="text-gray-500">Pre-configured compliance bundles for your industry</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={<Package className="h-5 w-5 text-blue-600" />} title="Available Packs" value={packs.length.toString()} subtitle="Industry-specific" />
        <StatCard icon={<CheckCircle className="h-5 w-5 text-green-600" />} title="Provisioned" value={packs.filter(p => p.status === 'provisioned').length.toString()} subtitle="Ready to use" />
        <StatCard icon={<Zap className="h-5 w-5 text-purple-600" />} title="Regulations" value={packs.reduce((sum, p) => sum + p.regulations.length, 0).toString()} subtitle="Total across packs" />
        <StatCard icon={<Rocket className="h-5 w-5 text-orange-600" />} title="Setup Time" value="<1 hr" subtitle="30-min guided wizard" />
      </div>

      {/* Packs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {packs.map(pack => (
          <div key={pack.vertical} className="card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900">{pack.name}</h3>
              <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${statusColors[pack.status]}`}>{pack.status}</span>
            </div>
            <p className="text-sm text-gray-500 mb-4">{pack.description}</p>

            <div className="mb-4">
              <p className="text-xs font-medium text-gray-400 uppercase mb-2">Regulations</p>
              <div className="space-y-2">
                {pack.regulations.map(r => (
                  <div key={r.regulation} className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">{r.regulation}</span>
                    <span className={`text-xs font-medium ${priorityColors[r.priority]}`}>{r.priority}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mb-4">
              <p className="text-xs font-medium text-gray-400 uppercase mb-2">Policy Templates</p>
              <div className="space-y-1">
                {pack.policy_templates.map(t => (
                  <div key={t.name} className="text-sm text-gray-600">• {t.name}</div>
                ))}
              </div>
            </div>

            <button
              onClick={() => pack.status !== 'provisioned' && handleProvision(pack.vertical)}
              disabled={provisioning || pack.status === 'provisioned'}
              className={`w-full py-2 rounded-md text-sm font-medium ${pack.status === 'provisioned' ? 'bg-green-100 text-green-700 cursor-default' : 'bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50'}`}
            >
              {pack.status === 'provisioned' ? '✓ Provisioned' : provisioning ? 'Provisioning...' : 'Provision Pack'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

function StatCard({ icon, title, value, subtitle }: { icon: React.ReactNode; title: string; value: string; subtitle: string }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between"><p className="text-sm font-medium text-gray-500">{title}</p>{icon}</div>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
      <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
    </div>
  )
}
