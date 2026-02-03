'use client'

import * as React from 'react'
import Link from 'next/link'
import { clsx } from 'clsx'
import {
  FolderOpen,
  GitBranch,
  AlertTriangle,
  Search,
  Plus,
  RefreshCw,
  Shield,
  Database,
  Settings,
  HelpCircle,
  ArrowRight,
} from 'lucide-react'

type EmptyStateVariant =
  | 'no-results'
  | 'no-data'
  | 'no-repositories'
  | 'no-regulations'
  | 'no-issues'
  | 'error'
  | 'access-denied'
  | 'configuration-needed'
  | 'custom'

interface EmptyStateAction {
  label: string
  href?: string
  onClick?: () => void
  variant?: 'primary' | 'secondary'
  icon?: React.ReactNode
}

interface EmptyStateProps {
  variant?: EmptyStateVariant
  title?: string
  description?: string
  icon?: React.ReactNode
  actions?: EmptyStateAction[]
  className?: string
  children?: React.ReactNode
}

// Illustrations for each variant
function NoResultsIllustration() {
  return (
    <svg className="w-32 h-32 text-gray-300 dark:text-gray-600" viewBox="0 0 128 128" fill="none">
      <circle cx="52" cy="52" r="36" stroke="currentColor" strokeWidth="6" />
      <line x1="78" y1="78" x2="108" y2="108" stroke="currentColor" strokeWidth="6" strokeLinecap="round" />
      <line x1="40" y1="46" x2="64" y2="46" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
      <line x1="40" y1="58" x2="56" y2="58" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
    </svg>
  )
}

function NoDataIllustration() {
  return (
    <svg className="w-32 h-32 text-gray-300 dark:text-gray-600" viewBox="0 0 128 128" fill="none">
      <rect x="24" y="16" width="80" height="96" rx="4" stroke="currentColor" strokeWidth="4" />
      <rect x="36" y="32" width="56" height="8" rx="2" fill="currentColor" opacity="0.3" />
      <rect x="36" y="48" width="40" height="8" rx="2" fill="currentColor" opacity="0.3" />
      <rect x="36" y="64" width="48" height="8" rx="2" fill="currentColor" opacity="0.3" />
      <circle cx="64" cy="88" r="12" stroke="currentColor" strokeWidth="3" />
      <path d="M64 82v12M64 82l4 4M64 82l-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function ErrorIllustration() {
  return (
    <svg className="w-32 h-32 text-red-300 dark:text-red-600" viewBox="0 0 128 128" fill="none">
      <circle cx="64" cy="64" r="48" stroke="currentColor" strokeWidth="4" />
      <path d="M64 40v32" stroke="currentColor" strokeWidth="6" strokeLinecap="round" />
      <circle cx="64" cy="88" r="4" fill="currentColor" />
    </svg>
  )
}

function AccessDeniedIllustration() {
  return (
    <svg className="w-32 h-32 text-yellow-300 dark:text-yellow-600" viewBox="0 0 128 128" fill="none">
      <rect x="32" y="48" width="64" height="56" rx="4" stroke="currentColor" strokeWidth="4" />
      <path d="M48 48V36a16 16 0 1132 0v12" stroke="currentColor" strokeWidth="4" />
      <circle cx="64" cy="76" r="8" fill="currentColor" />
      <path d="M64 84v12" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
    </svg>
  )
}

const variantConfig: Record<EmptyStateVariant, {
  icon: React.ReactNode
  illustration: React.ReactNode
  title: string
  description: string
  actions?: EmptyStateAction[]
}> = {
  'no-results': {
    icon: <Search className="h-6 w-6" />,
    illustration: <NoResultsIllustration />,
    title: 'No results found',
    description: 'Try adjusting your search or filter to find what you\'re looking for.',
    actions: [
      { label: 'Clear filters', variant: 'secondary', icon: <RefreshCw className="h-4 w-4" /> },
    ],
  },
  'no-data': {
    icon: <Database className="h-6 w-6" />,
    illustration: <NoDataIllustration />,
    title: 'No data yet',
    description: 'Start by adding your first item to see it here.',
    actions: [
      { label: 'Get started', variant: 'primary', icon: <Plus className="h-4 w-4" /> },
    ],
  },
  'no-repositories': {
    icon: <GitBranch className="h-6 w-6" />,
    illustration: <NoDataIllustration />,
    title: 'No repositories connected',
    description: 'Connect your repositories to start monitoring compliance.',
    actions: [
      { label: 'Connect repository', href: '/dashboard/repositories/connect', variant: 'primary', icon: <Plus className="h-4 w-4" /> },
      { label: 'Learn more', href: '/docs/guides/connecting-repositories', variant: 'secondary', icon: <HelpCircle className="h-4 w-4" /> },
    ],
  },
  'no-regulations': {
    icon: <Shield className="h-6 w-6" />,
    illustration: <NoDataIllustration />,
    title: 'No regulations configured',
    description: 'Add regulations to define your compliance requirements.',
    actions: [
      { label: 'Add regulation', href: '/dashboard/regulations/add', variant: 'primary', icon: <Plus className="h-4 w-4" /> },
      { label: 'Browse templates', href: '/dashboard/regulations/templates', variant: 'secondary' },
    ],
  },
  'no-issues': {
    icon: <AlertTriangle className="h-6 w-6" />,
    illustration: <NoDataIllustration />,
    title: 'All clear!',
    description: 'No compliance issues found. Your repositories are in good shape.',
  },
  'error': {
    icon: <AlertTriangle className="h-6 w-6" />,
    illustration: <ErrorIllustration />,
    title: 'Something went wrong',
    description: 'We encountered an error loading this content. Please try again.',
    actions: [
      { label: 'Retry', variant: 'primary', icon: <RefreshCw className="h-4 w-4" /> },
      { label: 'Report issue', variant: 'secondary' },
    ],
  },
  'access-denied': {
    icon: <Shield className="h-6 w-6" />,
    illustration: <AccessDeniedIllustration />,
    title: 'Access denied',
    description: 'You don\'t have permission to view this content.',
    actions: [
      { label: 'Request access', variant: 'primary' },
      { label: 'Go back', variant: 'secondary' },
    ],
  },
  'configuration-needed': {
    icon: <Settings className="h-6 w-6" />,
    illustration: <NoDataIllustration />,
    title: 'Configuration required',
    description: 'Complete the setup to start using this feature.',
    actions: [
      { label: 'Configure', href: '/dashboard/settings', variant: 'primary', icon: <Settings className="h-4 w-4" /> },
    ],
  },
  'custom': {
    icon: <FolderOpen className="h-6 w-6" />,
    illustration: <NoDataIllustration />,
    title: 'Nothing here',
    description: 'This area is empty.',
  },
}

export function EmptyState({
  variant = 'no-data',
  title,
  description,
  icon,
  actions,
  className,
  children,
}: EmptyStateProps) {
  const config = variantConfig[variant]
  
  const displayTitle = title || config.title
  const displayDescription = description || config.description
  const displayActions = actions || config.actions || []
  
  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center py-12 px-4 text-center',
        className
      )}
    >
      {/* Illustration */}
      <div className="mb-6">
        {icon || config.illustration}
      </div>
      
      {/* Content */}
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        {displayTitle}
      </h3>
      <p className="text-gray-500 dark:text-gray-400 max-w-md mb-6">
        {displayDescription}
      </p>
      
      {/* Actions */}
      {displayActions.length > 0 && (
        <div className="flex items-center gap-3 flex-wrap justify-center">
          {displayActions.map((action, index) => {
            const buttonClasses = clsx(
              'inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
              action.variant === 'primary'
                ? 'bg-primary-600 text-white hover:bg-primary-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
            )
            
            if (action.href) {
              return (
                <Link key={index} href={action.href} className={buttonClasses}>
                  {action.icon}
                  {action.label}
                  {action.variant === 'primary' && <ArrowRight className="h-4 w-4" />}
                </Link>
              )
            }
            
            return (
              <button key={index} onClick={action.onClick} className={buttonClasses}>
                {action.icon}
                {action.label}
              </button>
            )
          })}
        </div>
      )}
      
      {/* Custom children */}
      {children}
    </div>
  )
}

// Pre-built empty states for common scenarios
export function NoSearchResults({ onClear }: { onClear?: () => void }) {
  return (
    <EmptyState
      variant="no-results"
      actions={onClear ? [{ label: 'Clear search', onClick: onClear, variant: 'secondary', icon: <RefreshCw className="h-4 w-4" /> }] : undefined}
    />
  )
}

export function NoRepositories() {
  return <EmptyState variant="no-repositories" />
}

export function NoRegulations() {
  return <EmptyState variant="no-regulations" />
}

export function NoIssues() {
  return <EmptyState variant="no-issues" />
}

export function ErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <EmptyState
      variant="error"
      actions={onRetry ? [{ label: 'Try again', onClick: onRetry, variant: 'primary', icon: <RefreshCw className="h-4 w-4" /> }] : undefined}
    />
  )
}

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="animate-spin rounded-full h-12 w-12 border-4 border-gray-200 dark:border-gray-700 border-t-primary-600 mb-4" />
      <p className="text-gray-500 dark:text-gray-400">{message}</p>
    </div>
  )
}
