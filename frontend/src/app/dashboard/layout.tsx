'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  Shield,
  LayoutDashboard,
  FileText,
  Code,
  AlertTriangle,
  Settings,
  Bell,
  Search,
  FlaskConical,
  Building2,
  Activity,
  DollarSign,
  Lock,
  Globe,
  Store,
  Package,
  Beaker,
  MessageSquare,
  Brain,
  Calendar,
  ShieldCheck,
  Terminal,
  Bot,
  Crosshair,
  GitPullRequest,
  Gauge,
  LogOut,
  ChevronDown,
} from 'lucide-react'
import { clsx } from 'clsx'
import { CardErrorBoundary } from '@/components/ErrorBoundary'
import { ThemeToggle } from '@/components/ThemeToggle'
import { RealTimeProvider, LiveIndicator } from '@/components/ui/RealTime'
import { useAuth } from '@/contexts/auth'
import { api, searchApi, notificationsApi } from '@/lib/api'

interface NavigationItem {
  name: string
  href: string
  icon: typeof LayoutDashboard
  feature?: string
  experimental?: boolean
}

interface FeatureStatus {
  experimental_enabled: boolean
  flags: Array<{ name: string; enabled: boolean }>
}

const navigation: NavigationItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Regulations', href: '/dashboard/regulations', icon: FileText },
  { name: 'Repositories', href: '/dashboard/repositories', icon: Code },
  { name: 'Compliance Actions', href: '/dashboard/actions', icon: AlertTriangle },
  { name: 'Audit Trail', href: '/dashboard/audit', icon: FileText },
  { name: 'Testing Suite', href: '/dashboard/testing', icon: FlaskConical },
  { name: 'Architecture Advisor', href: '/dashboard/architecture-advisor', icon: Building2 },
  { name: 'Drift Detection', href: '/dashboard/drift-detection', icon: Activity, feature: 'drift_detection' },
  { name: 'Cost Calculator', href: '/dashboard/cost-calculator', icon: DollarSign },
  { name: 'Evidence Vault', href: '/dashboard/evidence-vault', icon: Lock, feature: 'evidence_vault' },
  { name: 'Federated Intel', href: '/dashboard/federated-intel', icon: Globe, feature: 'federated_intel' },
  { name: 'Marketplace', href: '/dashboard/marketplace', icon: Store },
  { name: 'Industry Packs', href: '/dashboard/industry-packs', icon: Package },
  { name: 'Sandbox', href: '/dashboard/compliance-sandbox', icon: Beaker, experimental: true },
  { name: 'Compliance Query', href: '/dashboard/nl-query', icon: MessageSquare },
  { name: 'Multi-LLM Engine', href: '/dashboard/multi-llm', icon: Brain, feature: 'multi_llm' },
  { name: 'Impact Timeline', href: '/dashboard/impact-timeline', icon: Calendar },
  { name: 'Audit Autopilot', href: '/dashboard/audit-autopilot', icon: ShieldCheck },
  { name: 'Policy SDK', href: '/dashboard/policy-sdk', icon: Terminal },
  { name: 'IDE Co-Pilot', href: '/dashboard/ide-copilot', icon: Bot },
  { name: 'Impact Simulator', href: '/dashboard/impact-simulator', icon: Crosshair, feature: 'impact_simulator' },
  { name: 'Remediation', href: '/dashboard/remediation-workflow', icon: GitPullRequest },
  { name: 'Posture Score', href: '/dashboard/posture-scoring', icon: Gauge, feature: 'posture_scoring' },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const [sidebarOpen] = useState(true)
  const { user, logout } = useAuth()
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const [featureStatus, setFeatureStatus] = useState<FeatureStatus | null>(null)
  const userMenuRef = useRef<HTMLDivElement>(null)

  // Close menus on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  useEffect(() => {
    let active = true
    api
      .get<FeatureStatus>('/status/features')
      .then((response) => {
        if (active) setFeatureStatus(response.data)
      })
      .catch(() => {
        if (active) {
          setFeatureStatus({ experimental_enabled: false, flags: [] })
        }
      })
    return () => {
      active = false
    }
  }, [])

  const enabledFlags = new Set(
    featureStatus?.flags.filter((flag) => flag.enabled).map((flag) => flag.name) ?? []
  )
  const isAvailable = (item: NavigationItem) => {
    if (item.feature) return enabledFlags.has(item.feature)
    if (item.experimental) return featureStatus?.experimental_enabled === true
    return true
  }
  const visibleNavigation = navigation.filter(isAvailable)
  const currentNavigationItem = navigation.find((item) => pathname === item.href)
  const currentFeatureDisabled =
    currentNavigationItem !== undefined && !isAvailable(currentNavigationItem)

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U'
  const displayName = user?.full_name || 'User'
  const displayEmail = user?.email || ''

  return (
    <RealTimeProvider>
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex flex-col bg-gray-900 transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-20'
        )}
      >
        {/* Logo */}
        <div className="flex h-16 items-center px-6 border-b border-gray-800">
          <Shield className="h-8 w-8 text-primary-500" />
          {sidebarOpen && (
            <span className="ml-3 text-lg font-bold text-white">ComplianceAgent</span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {visibleNavigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={clsx(
                  'flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                )}
              >
                <item.icon className="h-5 w-5 flex-shrink-0" />
                {sidebarOpen && <span className="ml-3">{item.name}</span>}
              </Link>
            )
          })}
        </nav>

        {/* User */}
        <div className="border-t border-gray-800 p-4" ref={userMenuRef}>
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex w-full items-center rounded-lg p-1 text-left hover:bg-gray-800 transition-colors"
            >
              <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-medium text-sm">
                {initials}
              </div>
              {sidebarOpen && (
                <>
                  <div className="ml-3 flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{displayName}</p>
                    <p className="text-xs text-gray-400 truncate">{displayEmail}</p>
                  </div>
                  <ChevronDown className={clsx('h-4 w-4 text-gray-400 transition-transform', userMenuOpen && 'rotate-180')} />
                </>
              )}
            </button>

            {userMenuOpen && (
              <div className="absolute bottom-full left-0 mb-2 w-56 rounded-lg bg-gray-800 border border-gray-700 shadow-lg py-1">
                <Link
                  href="/dashboard/settings"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex items-center px-4 py-2 text-sm text-gray-300 hover:bg-gray-700"
                >
                  <Settings className="h-4 w-4 mr-3" />
                  Settings
                </Link>
                <button
                  onClick={async () => { setUserMenuOpen(false); await logout() }}
                  className="flex w-full items-center px-4 py-2 text-sm text-red-400 hover:bg-gray-700"
                >
                  <LogOut className="h-4 w-4 mr-3" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className={clsx('transition-all duration-300', sidebarOpen ? 'ml-64' : 'ml-20')}>
        {/* Header */}
        <header className="sticky top-0 z-40 flex h-16 items-center gap-x-4 border-b border-gray-200 bg-white px-6">
          {/* Search */}
          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <HeaderSearch />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-x-4">
            <ThemeToggle />
            <LiveIndicator className="h-2 w-2" />
            <NotificationBell />
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          <CardErrorBoundary>
            {currentFeatureDisabled ? (
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-amber-900">
                <h1 className="text-lg font-semibold">Feature unavailable</h1>
                <p className="mt-2 text-sm">
                  This preview or experimental capability is disabled in the current
                  environment because it does not provide durable production storage.
                </p>
              </div>
            ) : (
              children
            )}
          </CardErrorBoundary>
        </main>
      </div>
    </div>
    </RealTimeProvider>
  )
}

// ---------------------------------------------------------------------------
// HeaderSearch — debounced global search with keyboard navigation
// ---------------------------------------------------------------------------

interface SearchResult {
  id: string
  type: string
  title: string
  description?: string
  url: string
}

function HeaderSearch() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [selectedIdx, setSelectedIdx] = useState(-1)
  const [error, setError] = useState<string | null>(null)
  const ref = useRef<HTMLDivElement>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const doSearch = useCallback(async (q: string) => {
    if (q.length < 2) { setResults([]); setOpen(false); return }
    setLoading(true)
    setError(null)
    try {
      const res = await searchApi.search(q, { limit: 10 })
      setResults(res.data.items)
      setOpen(true)
    } catch {
      setError('Search failed')
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  const handleChange = (val: string) => {
    setQuery(val)
    setSelectedIdx(-1)
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => doSearch(val), 300)
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIdx(i => Math.min(i + 1, results.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIdx(i => Math.max(i - 1, 0)) }
    else if (e.key === 'Enter' && selectedIdx >= 0 && results[selectedIdx]) {
      e.preventDefault()
      router.push(results[selectedIdx].url)
      setOpen(false)
    } else if (e.key === 'Escape') setOpen(false)
  }

  const typeIcon: Record<string, string> = { regulation: '📜', requirement: '📋', action: '⚡', repository: '💻' }

  return (
    <div className="relative flex flex-1 items-center" ref={ref}>
      <Search className="pointer-events-none absolute left-3 h-5 w-5 text-gray-400" />
      <input
        type="text"
        value={query}
        onChange={e => handleChange(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        onKeyDown={handleKey}
        placeholder="Search regulations, requirements, actions..."
        className="h-10 w-full max-w-md rounded-lg border border-gray-200 pl-10 pr-4 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
      />
      {open && (
        <div className="absolute left-0 top-12 w-full max-w-md rounded-lg bg-white border border-gray-200 shadow-lg z-50 max-h-80 overflow-y-auto">
          {loading && <div className="px-4 py-3 text-sm text-gray-500">Searching...</div>}
          {error && <div className="px-4 py-3 text-sm text-red-500">{error}</div>}
          {!loading && !error && results.length === 0 && query.length >= 2 && (
            <div className="px-4 py-6 text-center text-sm text-gray-500">No results found</div>
          )}
          {results.map((r, i) => (
            <Link
              key={r.id}
              href={r.url}
              onClick={() => setOpen(false)}
              className={clsx(
                'flex items-start gap-3 px-4 py-3 text-sm hover:bg-gray-50 transition-colors',
                i === selectedIdx && 'bg-primary-50'
              )}
            >
              <span className="text-lg">{typeIcon[r.type] || '🔍'}</span>
              <div className="min-w-0">
                <p className="font-medium text-gray-900 truncate">{r.title}</p>
                {r.description && <p className="text-gray-500 text-xs truncate">{r.description}</p>}
                <span className="text-xs text-primary-600 capitalize">{r.type}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// NotificationBell — live unread count, paginated inbox, mark read, delete
// ---------------------------------------------------------------------------

interface NotifItem {
  id: string
  notification_type: string
  title: string
  message: string
  priority: string
  is_read: boolean
  action_url: string | null
  created_at: string
}

function NotificationBell() {
  const [open, setOpen] = useState(false)
  const [unread, setUnread] = useState(0)
  const [items, setItems] = useState<NotifItem[]>([])
  const [loading, setLoading] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const fetchUnread = useCallback(async () => {
    try {
      const res = await notificationsApi.unreadCount()
      setUnread(res.data.unread)
    } catch { /* silent */ }
  }, [])

  const fetchItems = useCallback(async () => {
    setLoading(true)
    try {
      const res = await notificationsApi.list({ limit: 20 })
      setItems(res.data.items)
    } catch { /* silent */ }
    setLoading(false)
  }, [])

  // Poll every 30 seconds
  useEffect(() => {
    fetchUnread()
    const interval = setInterval(fetchUnread, 30_000)
    return () => clearInterval(interval)
  }, [fetchUnread])

  useEffect(() => {
    if (open) fetchItems()
  }, [open, fetchItems])

  const markRead = async (id: string) => {
    await notificationsApi.markRead(id)
    setItems(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))
    setUnread(prev => Math.max(0, prev - 1))
  }

  const markAllRead = async () => {
    await notificationsApi.markAllRead()
    setItems(prev => prev.map(n => ({ ...n, is_read: true })))
    setUnread(0)
  }

  const deleteItem = async (id: string) => {
    await notificationsApi.delete(id)
    const item = items.find(n => n.id === id)
    setItems(prev => prev.filter(n => n.id !== id))
    if (item && !item.is_read) setUnread(prev => Math.max(0, prev - 1))
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="relative rounded-full p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
      >
        <Bell className="h-5 w-5" />
        {unread > 0 && (
          <span className="absolute right-0.5 top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-96 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-lg z-50">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Notifications</h3>
            {unread > 0 && (
              <button onClick={markAllRead} className="text-xs text-primary-600 hover:text-primary-500">
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto divide-y divide-gray-100 dark:divide-gray-700">
            {loading && <div className="px-4 py-6 text-center text-sm text-gray-500">Loading...</div>}
            {!loading && items.length === 0 && (
              <div className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">
                No notifications
              </div>
            )}
            {items.map(n => (
              <div
                key={n.id}
                className={clsx(
                  'px-4 py-3 flex gap-3 items-start group',
                  !n.is_read && 'bg-primary-50 dark:bg-gray-750'
                )}
              >
                <div className="min-w-0 flex-1">
                  <p className={clsx('text-sm', !n.is_read ? 'font-semibold text-gray-900 dark:text-white' : 'text-gray-700 dark:text-gray-300')}>
                    {n.title}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.message}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] text-gray-400">{new Date(n.created_at).toLocaleDateString()}</span>
                    {n.action_url && (
                      <Link
                        href={n.action_url}
                        onClick={() => { if (!n.is_read) markRead(n.id); setOpen(false) }}
                        className="text-[10px] text-primary-600 hover:underline"
                      >
                        View →
                      </Link>
                    )}
                  </div>
                </div>
                <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {!n.is_read && (
                    <button onClick={() => markRead(n.id)} className="text-xs text-gray-400 hover:text-primary-500" title="Mark read">
                      ✓
                    </button>
                  )}
                  <button onClick={() => deleteItem(n.id)} className="text-xs text-gray-400 hover:text-red-500" title="Delete">
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
            <Link
              href="/dashboard/settings"
              onClick={() => setOpen(false)}
              className="text-xs text-primary-600 hover:text-primary-500"
            >
              Notification settings →
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
