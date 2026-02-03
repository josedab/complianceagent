'use client'

import * as React from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { Search, X, FileText, GitBranch, AlertTriangle, History, Loader2 } from 'lucide-react'
import { clsx } from 'clsx'
import { useRouter } from 'next/navigation'

type SearchResultType = 'regulation' | 'repository' | 'issue' | 'audit'

interface SearchResult {
  id: string
  type: SearchResultType
  title: string
  subtitle?: string
  metadata?: Record<string, string>
  href: string
}

interface GlobalSearchProps {
  placeholder?: string
  className?: string
}

const typeIcons: Record<SearchResultType, React.ReactNode> = {
  regulation: <FileText className="h-4 w-4" />,
  repository: <GitBranch className="h-4 w-4" />,
  issue: <AlertTriangle className="h-4 w-4" />,
  audit: <History className="h-4 w-4" />,
}

const typeLabels: Record<SearchResultType, string> = {
  regulation: 'Regulation',
  repository: 'Repository',
  issue: 'Issue',
  audit: 'Audit Entry',
}

const typeColors: Record<SearchResultType, string> = {
  regulation: 'text-blue-500 bg-blue-100 dark:bg-blue-900/30',
  repository: 'text-purple-500 bg-purple-100 dark:bg-purple-900/30',
  issue: 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/30',
  audit: 'text-gray-500 bg-gray-100 dark:bg-gray-800',
}

// Mock search function - replace with real API call
async function performSearch(query: string): Promise<SearchResult[]> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 300))
  
  if (!query.trim()) return []
  
  const q = query.toLowerCase()
  
  // Mock results
  const allResults: SearchResult[] = [
    {
      id: '1',
      type: 'regulation',
      title: 'GDPR',
      subtitle: 'General Data Protection Regulation',
      metadata: { jurisdiction: 'EU' },
      href: '/dashboard/regulations/gdpr',
    },
    {
      id: '2',
      type: 'regulation',
      title: 'CCPA',
      subtitle: 'California Consumer Privacy Act',
      metadata: { jurisdiction: 'US-CA' },
      href: '/dashboard/regulations/ccpa',
    },
    {
      id: '3',
      type: 'regulation',
      title: 'HIPAA',
      subtitle: 'Health Insurance Portability and Accountability Act',
      metadata: { jurisdiction: 'US' },
      href: '/dashboard/regulations/hipaa',
    },
    {
      id: '4',
      type: 'repository',
      title: 'acme/web-app',
      subtitle: 'Main web application',
      metadata: { score: '87%' },
      href: '/dashboard/repositories/repo-1',
    },
    {
      id: '5',
      type: 'repository',
      title: 'acme/api-service',
      subtitle: 'Backend API service',
      metadata: { score: '92%' },
      href: '/dashboard/repositories/repo-2',
    },
    {
      id: '6',
      type: 'issue',
      title: 'Missing data encryption',
      subtitle: 'GDPR Article 32 violation',
      metadata: { severity: 'Critical' },
      href: '/dashboard/actions/issue-1',
    },
    {
      id: '7',
      type: 'issue',
      title: 'Incomplete consent flow',
      subtitle: 'GDPR Article 7 violation',
      metadata: { severity: 'High' },
      href: '/dashboard/actions/issue-2',
    },
  ]
  
  return allResults.filter(
    (r) =>
      r.title.toLowerCase().includes(q) ||
      r.subtitle?.toLowerCase().includes(q)
  )
}

export function GlobalSearch({ placeholder = 'Search everything...', className }: GlobalSearchProps) {
  const [open, setOpen] = React.useState(false)
  const [query, setQuery] = React.useState('')
  const [results, setResults] = React.useState<SearchResult[]>([])
  const [loading, setLoading] = React.useState(false)
  const [selectedIndex, setSelectedIndex] = React.useState(0)
  const [activeFilter, setActiveFilter] = React.useState<SearchResultType | 'all'>('all')
  const inputRef = React.useRef<HTMLInputElement>(null)
  const router = useRouter()
  
  // Debounced search
  React.useEffect(() => {
    if (!query.trim()) {
      setResults([])
      return
    }
    
    setLoading(true)
    const timer = setTimeout(async () => {
      const searchResults = await performSearch(query)
      setResults(searchResults)
      setLoading(false)
      setSelectedIndex(0)
    }, 200)
    
    return () => clearTimeout(timer)
  }, [query])
  
  // Reset state when opening
  React.useEffect(() => {
    if (open) {
      setQuery('')
      setResults([])
      setSelectedIndex(0)
      setActiveFilter('all')
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }, [open])
  
  // Keyboard shortcut to open
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && !e.metaKey && !e.ctrlKey) {
        const target = e.target as HTMLElement
        if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
          e.preventDefault()
          setOpen(true)
        }
      }
    }
    
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])
  
  const filteredResults = React.useMemo(() => {
    if (activeFilter === 'all') return results
    return results.filter((r) => r.type === activeFilter)
  }, [results, activeFilter])
  
  const handleSelect = (result: SearchResult) => {
    setOpen(false)
    router.push(result.href)
  }
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex((i) => Math.min(i + 1, filteredResults.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex((i) => Math.max(i - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (filteredResults[selectedIndex]) {
          handleSelect(filteredResults[selectedIndex])
        }
        break
    }
  }
  
  const filters: Array<{ value: SearchResultType | 'all'; label: string }> = [
    { value: 'all', label: 'All' },
    { value: 'regulation', label: 'Regulations' },
    { value: 'repository', label: 'Repositories' },
    { value: 'issue', label: 'Issues' },
    { value: 'audit', label: 'Audit' },
  ]
  
  // Group results by type
  const groupedResults = React.useMemo(() => {
    const groups: Partial<Record<SearchResultType, SearchResult[]>> = {}
    for (const result of filteredResults) {
      if (!groups[result.type]) {
        groups[result.type] = []
      }
      groups[result.type]!.push(result)
    }
    return groups
  }, [filteredResults])
  
  return (
    <>
      {/* Trigger */}
      <button
        onClick={() => setOpen(true)}
        data-search-input
        className={clsx(
          'flex items-center gap-2 w-full max-w-md px-3 py-2 text-sm text-left',
          'bg-gray-100 dark:bg-gray-800 rounded-lg',
          'text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors',
          className
        )}
      >
        <Search className="h-4 w-4" />
        <span className="flex-1">{placeholder}</span>
        <kbd className="hidden md:inline-flex items-center px-1.5 py-0.5 text-xs bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
          /
        </kbd>
      </button>
      
      {/* Dialog */}
      <Dialog.Root open={open} onOpenChange={setOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
          <Dialog.Content
            className="fixed left-1/2 top-[15%] -translate-x-1/2 w-full max-w-2xl bg-white dark:bg-gray-900 rounded-xl shadow-2xl z-50 overflow-hidden border border-gray-200 dark:border-gray-700"
            onKeyDown={handleKeyDown}
          >
            {/* Search input */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
              <Search className="h-5 w-5 text-gray-400" />
              <input
                ref={inputRef}
                type="text"
                placeholder={placeholder}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1 bg-transparent outline-none text-gray-900 dark:text-white placeholder-gray-400"
              />
              {loading && <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />}
              <Dialog.Close className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded hover:bg-gray-100 dark:hover:bg-gray-800">
                <X className="h-4 w-4" />
              </Dialog.Close>
            </div>
            
            {/* Filters */}
            <div className="flex items-center gap-1 px-4 py-2 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
              {filters.map((filter) => (
                <button
                  key={filter.value}
                  onClick={() => setActiveFilter(filter.value)}
                  className={clsx(
                    'px-3 py-1 text-sm rounded-full whitespace-nowrap transition-colors',
                    activeFilter === filter.value
                      ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                  )}
                >
                  {filter.label}
                </button>
              ))}
            </div>
            
            {/* Results */}
            <div className="max-h-96 overflow-y-auto">
              {query && filteredResults.length === 0 && !loading && (
                <div className="px-4 py-8 text-center text-gray-500">
                  <p>No results found for &quot;{query}&quot;</p>
                  <p className="text-sm mt-1">Try different keywords or filters</p>
                </div>
              )}
              
              {!query && (
                <div className="px-4 py-8 text-center text-gray-500">
                  <p>Start typing to search</p>
                  <p className="text-sm mt-1">Search regulations, repositories, issues, and more</p>
                </div>
              )}
              
              {Object.entries(groupedResults).map(([type, items]) => (
                <div key={type}>
                  <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50 dark:bg-gray-800/50">
                    {typeLabels[type as SearchResultType]}
                  </div>
                  {items!.map((result) => {
                    const globalIndex = filteredResults.indexOf(result)
                    const isSelected = globalIndex === selectedIndex
                    
                    return (
                      <button
                        key={result.id}
                        onClick={() => handleSelect(result)}
                        className={clsx(
                          'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors',
                          isSelected
                            ? 'bg-primary-50 dark:bg-primary-900/20'
                            : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                        )}
                      >
                        <span className={clsx('p-2 rounded-lg', typeColors[result.type])}>
                          {typeIcons[result.type]}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-gray-900 dark:text-white truncate">
                            {result.title}
                          </div>
                          {result.subtitle && (
                            <div className="text-sm text-gray-500 truncate">{result.subtitle}</div>
                          )}
                        </div>
                        {result.metadata && (
                          <div className="text-xs text-gray-400">
                            {Object.values(result.metadata)[0]}
                          </div>
                        )}
                      </button>
                    )
                  })}
                </div>
              ))}
            </div>
            
            {/* Footer */}
            <div className="flex items-center justify-between px-4 py-2 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">↑</kbd>
                  <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">↓</kbd>
                  navigate
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">↵</kbd>
                  select
                </span>
              </div>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">esc</kbd>
                close
              </span>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  )
}
