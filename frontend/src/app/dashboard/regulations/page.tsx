'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { Search, FileText, Calendar, Globe, ChevronRight } from 'lucide-react'
import { useRegulations } from '@/hooks/useApi'
import { RegulationsSkeleton } from '@/components/ui/Skeleton'
import type { Regulation, Jurisdiction } from '@/types'

const frameworkOptions: Array<{ value: string; label: string }> = [
  { value: 'All', label: 'All Frameworks' },
  { value: 'GDPR', label: 'GDPR' },
  { value: 'CCPA', label: 'CCPA' },
  { value: 'EU_AI_ACT', label: 'EU AI Act' },
  { value: 'HIPAA', label: 'HIPAA' },
  { value: 'PCI_DSS', label: 'PCI-DSS' },
  { value: 'SOX', label: 'SOX' },
  { value: 'NIS2', label: 'NIS2' },
]

const jurisdictionOptions: Array<{ value: string; label: string }> = [
  { value: 'All', label: 'All Jurisdictions' },
  { value: 'EU', label: 'European Union' },
  { value: 'US_FEDERAL', label: 'US Federal' },
  { value: 'US_CALIFORNIA', label: 'California' },
  { value: 'UK', label: 'United Kingdom' },
  { value: 'GLOBAL', label: 'Global' },
]

export default function RegulationsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFramework, setSelectedFramework] = useState('All')
  const [selectedJurisdiction, setSelectedJurisdiction] = useState('All')

  const { data: regulations, loading, error } = useRegulations()

  const filteredRegulations = useMemo(() => {
    if (!regulations) return []
    
    return regulations.filter((reg) => {
      const matchesSearch = 
        reg.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        reg.short_name.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesFramework = 
        selectedFramework === 'All' || reg.framework === selectedFramework
      const matchesJurisdiction = 
        selectedJurisdiction === 'All' || reg.jurisdiction === selectedJurisdiction
      return matchesSearch && matchesFramework && matchesJurisdiction
    })
  }, [regulations, searchQuery, selectedFramework, selectedJurisdiction])

  if (loading) {
    return <RegulationsSkeleton />
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Regulations</h1>
          <p className="text-gray-500">Monitor and track regulatory frameworks</p>
        </div>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 text-sm">
            Unable to load from server. Showing available data.
          </p>
        </div>
      )}

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search regulations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="flex gap-4">
            <select
              value={selectedFramework}
              onChange={(e) => setSelectedFramework(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {frameworkOptions.map((fw) => (
                <option key={fw.value} value={fw.value}>{fw.label}</option>
              ))}
            </select>
            <select
              value={selectedJurisdiction}
              onChange={(e) => setSelectedJurisdiction(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {jurisdictionOptions.map((j) => (
                <option key={j.value} value={j.value}>{j.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Regulations List */}
      <div className="space-y-4">
        {filteredRegulations.map((regulation) => (
          <RegulationCard key={regulation.id} regulation={regulation} />
        ))}

        {filteredRegulations.length === 0 && (
          <div className="card text-center py-12">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No regulations found matching your criteria</p>
          </div>
        )}
      </div>
    </div>
  )
}

function RegulationCard({ regulation }: { regulation: Regulation }) {
  const formatJurisdiction = (j: Jurisdiction): string => {
    const map: Record<Jurisdiction, string> = {
      EU: 'European Union',
      UK: 'United Kingdom',
      US_FEDERAL: 'US Federal',
      US_CALIFORNIA: 'California',
      US_NEW_YORK: 'New York',
      SINGAPORE: 'Singapore',
      SOUTH_KOREA: 'South Korea',
      CHINA: 'China',
      INDIA: 'India',
      GLOBAL: 'Global',
    }
    return map[j] || j
  }

  return (
    <Link href={`/dashboard/regulations/${regulation.id}`}>
      <div className="card hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-lg font-semibold text-gray-900">{regulation.short_name}</h3>
              <span className="status-badge status-compliant">
                active
              </span>
            </div>
            <p className="text-gray-600 mb-3">{regulation.name}</p>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <Globe className="h-4 w-4" />
                <span>{formatJurisdiction(regulation.jurisdiction)}</span>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>Effective: {new Date(regulation.effective_date).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center gap-1">
                <FileText className="h-4 w-4" />
                <span>v{regulation.version}</span>
              </div>
            </div>
          </div>
          <ChevronRight className="h-5 w-5 text-gray-400" />
        </div>
      </div>
    </Link>
  )
}
