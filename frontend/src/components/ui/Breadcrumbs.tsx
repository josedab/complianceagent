'use client'

import * as React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronRight, Home } from 'lucide-react'
import { clsx } from 'clsx'

interface BreadcrumbItem {
  label: string
  href?: string
  icon?: React.ReactNode
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[]
  showHome?: boolean
  separator?: React.ReactNode
  className?: string
}

// Route label mappings
const routeLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  regulations: 'Regulations',
  repositories: 'Repositories',
  actions: 'Actions',
  audit: 'Audit Trail',
  settings: 'Settings',
  login: 'Login',
  signup: 'Sign Up',
}

// Generate breadcrumbs from pathname
function generateBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split('/').filter(Boolean)
  const breadcrumbs: BreadcrumbItem[] = []
  
  let currentPath = ''
  
  for (const segment of segments) {
    currentPath += `/${segment}`
    
    // Check if this is a dynamic segment (UUID or similar)
    const isDynamic = /^[0-9a-f-]{8,}$/i.test(segment)
    
    const label = isDynamic
      ? 'Details'
      : routeLabels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1)
    
    breadcrumbs.push({
      label,
      href: currentPath,
    })
  }
  
  return breadcrumbs
}

export function Breadcrumbs({
  items,
  showHome = true,
  separator = <ChevronRight className="h-4 w-4 text-gray-400" />,
  className,
}: BreadcrumbsProps) {
  const pathname = usePathname()
  
  const breadcrumbs = items || generateBreadcrumbs(pathname)
  
  if (breadcrumbs.length === 0 && !showHome) return null
  
  return (
    <nav
      aria-label="Breadcrumb"
      className={clsx('flex items-center text-sm', className)}
    >
      <ol className="flex items-center gap-1">
        {showHome && (
          <li className="flex items-center">
            <Link
              href="/dashboard"
              className="flex items-center gap-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
            >
              <Home className="h-4 w-4" />
              <span className="sr-only">Home</span>
            </Link>
            {breadcrumbs.length > 0 && (
              <span className="mx-2">{separator}</span>
            )}
          </li>
        )}
        
        {breadcrumbs.map((item, index) => {
          const isLast = index === breadcrumbs.length - 1
          
          return (
            <li key={index} className="flex items-center">
              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                >
                  {item.icon && <span className="mr-1">{item.icon}</span>}
                  {item.label}
                </Link>
              ) : (
                <span className="text-gray-900 dark:text-white font-medium">
                  {item.icon && <span className="mr-1">{item.icon}</span>}
                  {item.label}
                </span>
              )}
              
              {!isLast && <span className="mx-2">{separator}</span>}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

// Hook to get current breadcrumbs
export function useBreadcrumbs(): BreadcrumbItem[] {
  const pathname = usePathname()
  return React.useMemo(() => generateBreadcrumbs(pathname), [pathname])
}

// Breadcrumb context for custom items
interface BreadcrumbContextValue {
  items: BreadcrumbItem[]
  setItems: (items: BreadcrumbItem[]) => void
  appendItem: (item: BreadcrumbItem) => void
  clearItems: () => void
}

const BreadcrumbContext = React.createContext<BreadcrumbContextValue | undefined>(undefined)

export function BreadcrumbProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<BreadcrumbItem[]>([])
  
  const appendItem = React.useCallback((item: BreadcrumbItem) => {
    setItems((prev) => [...prev, item])
  }, [])
  
  const clearItems = React.useCallback(() => {
    setItems([])
  }, [])
  
  return (
    <BreadcrumbContext.Provider value={{ items, setItems, appendItem, clearItems }}>
      {children}
    </BreadcrumbContext.Provider>
  )
}

export function useBreadcrumbContext() {
  const context = React.useContext(BreadcrumbContext)
  if (!context) {
    throw new Error('useBreadcrumbContext must be used within a BreadcrumbProvider')
  }
  return context
}

// Component to set custom breadcrumb for a page
export function SetBreadcrumb({ label, icon }: { label: string; icon?: React.ReactNode }) {
  const pathname = usePathname()
  const { setItems } = useBreadcrumbContext()
  
  React.useEffect(() => {
    const baseBreadcrumbs = generateBreadcrumbs(pathname)
    if (baseBreadcrumbs.length > 0) {
      baseBreadcrumbs[baseBreadcrumbs.length - 1] = {
        ...baseBreadcrumbs[baseBreadcrumbs.length - 1],
        label,
        icon,
      }
    }
    setItems(baseBreadcrumbs)
    
    return () => setItems([])
  }, [pathname, label, icon, setItems])
  
  return null
}
