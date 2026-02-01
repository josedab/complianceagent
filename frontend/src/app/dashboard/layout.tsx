'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Shield,
  LayoutDashboard,
  FileText,
  Code,
  AlertTriangle,
  Settings,
  Bell,
  Search,
} from 'lucide-react'
import { clsx } from 'clsx'
import { CardErrorBoundary } from '@/components/ErrorBoundary'
import { ThemeToggle } from '@/components/ThemeToggle'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Regulations', href: '/dashboard/regulations', icon: FileText },
  { name: 'Repositories', href: '/dashboard/repositories', icon: Code },
  { name: 'Compliance Actions', href: '/dashboard/actions', icon: AlertTriangle },
  { name: 'Audit Trail', href: '/dashboard/audit', icon: FileText },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const [sidebarOpen] = useState(true)

  return (
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
          {navigation.map((item) => {
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
        <div className="border-t border-gray-800 p-4">
          <div className="flex items-center">
            <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-medium">
              JB
            </div>
            {sidebarOpen && (
              <div className="ml-3">
                <p className="text-sm font-medium text-white">Jose Baena</p>
                <p className="text-xs text-gray-400">Admin</p>
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
            <div className="relative flex flex-1 items-center">
              <Search className="pointer-events-none absolute left-3 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search regulations, requirements, actions..."
                className="h-10 w-full max-w-md rounded-lg border border-gray-200 pl-10 pr-4 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-x-4">
            <ThemeToggle />
            <button className="relative rounded-full p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800">
              <Bell className="h-5 w-5" />
              <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          <CardErrorBoundary>
            {children}
          </CardErrorBoundary>
        </main>
      </div>
    </div>
  )
}
