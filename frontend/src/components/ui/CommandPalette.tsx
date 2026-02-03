'use client'

import * as React from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { useRouter } from 'next/navigation'
import {
  Search,
  Home,
  FileText,
  GitBranch,
  CheckSquare,
  History,
  Settings,
  Plus,
  RefreshCw,
  Download,
  Keyboard,
  ArrowRight,
} from 'lucide-react'
import { clsx } from 'clsx'

type CommandAction = {
  id: string
  title: string
  subtitle?: string
  icon: React.ReactNode
  shortcut?: string[]
  action: () => void
  section: 'navigation' | 'actions' | 'settings'
}

interface CommandPaletteContextValue {
  open: boolean
  setOpen: (open: boolean) => void
  registerAction: (action: CommandAction) => void
  unregisterAction: (id: string) => void
}

const CommandPaletteContext = React.createContext<CommandPaletteContextValue | undefined>(undefined)

export function useCommandPalette() {
  const context = React.useContext(CommandPaletteContext)
  if (!context) {
    throw new Error('useCommandPalette must be used within a CommandPaletteProvider')
  }
  return context
}

export function CommandPaletteProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false)
  const [customActions, setCustomActions] = React.useState<CommandAction[]>([])

  const registerAction = React.useCallback((action: CommandAction) => {
    setCustomActions((prev) => [...prev.filter((a) => a.id !== action.id), action])
  }, [])

  const unregisterAction = React.useCallback((id: string) => {
    setCustomActions((prev) => prev.filter((a) => a.id !== id))
  }, [])

  // Global keyboard shortcut
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <CommandPaletteContext.Provider value={{ open, setOpen, registerAction, unregisterAction }}>
      {children}
      <CommandPaletteDialog open={open} onOpenChange={setOpen} customActions={customActions} />
    </CommandPaletteContext.Provider>
  )
}

function CommandPaletteDialog({
  open,
  onOpenChange,
  customActions,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  customActions: CommandAction[]
}) {
  const router = useRouter()
  const [query, setQuery] = React.useState('')
  const [selectedIndex, setSelectedIndex] = React.useState(0)
  const inputRef = React.useRef<HTMLInputElement>(null)

  const baseActions: CommandAction[] = React.useMemo(
    () => [
      {
        id: 'nav-dashboard',
        title: 'Go to Dashboard',
        icon: <Home className="h-4 w-4" />,
        shortcut: ['G', 'D'],
        action: () => router.push('/dashboard'),
        section: 'navigation',
      },
      {
        id: 'nav-regulations',
        title: 'Go to Regulations',
        icon: <FileText className="h-4 w-4" />,
        shortcut: ['G', 'R'],
        action: () => router.push('/dashboard/regulations'),
        section: 'navigation',
      },
      {
        id: 'nav-repositories',
        title: 'Go to Repositories',
        icon: <GitBranch className="h-4 w-4" />,
        shortcut: ['G', 'P'],
        action: () => router.push('/dashboard/repositories'),
        section: 'navigation',
      },
      {
        id: 'nav-actions',
        title: 'Go to Actions',
        icon: <CheckSquare className="h-4 w-4" />,
        shortcut: ['G', 'A'],
        action: () => router.push('/dashboard/actions'),
        section: 'navigation',
      },
      {
        id: 'nav-audit',
        title: 'Go to Audit Trail',
        icon: <History className="h-4 w-4" />,
        shortcut: ['G', 'U'],
        action: () => router.push('/dashboard/audit'),
        section: 'navigation',
      },
      {
        id: 'nav-settings',
        title: 'Go to Settings',
        icon: <Settings className="h-4 w-4" />,
        shortcut: ['G', 'S'],
        action: () => router.push('/dashboard/settings'),
        section: 'navigation',
      },
      {
        id: 'action-new-repo',
        title: 'Connect Repository',
        subtitle: 'Add a new GitHub repository',
        icon: <Plus className="h-4 w-4" />,
        action: () => {
          router.push('/dashboard/repositories')
          // Could open a modal here
        },
        section: 'actions',
      },
      {
        id: 'action-scan',
        title: 'Run Compliance Scan',
        subtitle: 'Scan all repositories for issues',
        icon: <RefreshCw className="h-4 w-4" />,
        action: () => {
          // Trigger scan
          console.log('Triggering scan...')
        },
        section: 'actions',
      },
      {
        id: 'action-export',
        title: 'Export Audit Report',
        subtitle: 'Download compliance evidence',
        icon: <Download className="h-4 w-4" />,
        action: () => router.push('/dashboard/audit'),
        section: 'actions',
      },
      {
        id: 'settings-shortcuts',
        title: 'Keyboard Shortcuts',
        icon: <Keyboard className="h-4 w-4" />,
        shortcut: ['?'],
        action: () => {
          // Show shortcuts modal
          console.log('Show shortcuts')
        },
        section: 'settings',
      },
    ],
    [router]
  )

  const allActions = React.useMemo(
    () => [...baseActions, ...customActions],
    [baseActions, customActions]
  )

  const filteredActions = React.useMemo(() => {
    if (!query) return allActions
    const q = query.toLowerCase()
    return allActions.filter(
      (action) =>
        action.title.toLowerCase().includes(q) ||
        action.subtitle?.toLowerCase().includes(q)
    )
  }, [allActions, query])

  const groupedActions = React.useMemo(() => {
    const groups: Record<string, CommandAction[]> = {
      navigation: [],
      actions: [],
      settings: [],
    }
    filteredActions.forEach((action) => {
      groups[action.section].push(action)
    })
    return groups
  }, [filteredActions])

  // Reset selection when query changes
  React.useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  // Reset state when dialog opens
  React.useEffect(() => {
    if (open) {
      setQuery('')
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }, [open])

  const executeAction = (action: CommandAction) => {
    onOpenChange(false)
    action.action()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex((i) => Math.min(i + 1, filteredActions.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex((i) => Math.max(i - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (filteredActions[selectedIndex]) {
          executeAction(filteredActions[selectedIndex])
        }
        break
      case 'Escape':
        e.preventDefault()
        onOpenChange(false)
        break
    }
  }

  let currentIndex = 0

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content
          className="fixed left-1/2 top-[20%] -translate-x-1/2 w-full max-w-lg bg-white dark:bg-gray-900 rounded-xl shadow-2xl z-50 overflow-hidden border border-gray-200 dark:border-gray-700"
          onKeyDown={handleKeyDown}
        >
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <Search className="h-5 w-5 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Search commands..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 bg-transparent outline-none text-gray-900 dark:text-white placeholder-gray-400"
            />
            <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-500 bg-gray-100 dark:bg-gray-800 rounded">
              ESC
            </kbd>
          </div>

          {/* Results */}
          <div className="max-h-80 overflow-y-auto py-2">
            {filteredActions.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                <p>No commands found</p>
                <p className="text-sm mt-1">Try a different search term</p>
              </div>
            ) : (
              <>
                {groupedActions.navigation.length > 0 && (
                  <CommandGroup title="Navigation">
                    {groupedActions.navigation.map((action) => {
                      const index = currentIndex++
                      return (
                        <CommandItem
                          key={action.id}
                          action={action}
                          selected={index === selectedIndex}
                          onSelect={() => executeAction(action)}
                        />
                      )
                    })}
                  </CommandGroup>
                )}
                {groupedActions.actions.length > 0 && (
                  <CommandGroup title="Actions">
                    {groupedActions.actions.map((action) => {
                      const index = currentIndex++
                      return (
                        <CommandItem
                          key={action.id}
                          action={action}
                          selected={index === selectedIndex}
                          onSelect={() => executeAction(action)}
                        />
                      )
                    })}
                  </CommandGroup>
                )}
                {groupedActions.settings.length > 0 && (
                  <CommandGroup title="Settings">
                    {groupedActions.settings.map((action) => {
                      const index = currentIndex++
                      return (
                        <CommandItem
                          key={action.id}
                          action={action}
                          selected={index === selectedIndex}
                          onSelect={() => executeAction(action)}
                        />
                      )
                    })}
                  </CommandGroup>
                )}
              </>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-2 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">↑</kbd>
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">↓</kbd>
                to navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">↵</kbd>
                to select
              </span>
            </div>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">⌘</kbd>
              <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">K</kbd>
              to toggle
            </span>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

function CommandGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="px-2">
      <div className="px-2 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">
        {title}
      </div>
      {children}
    </div>
  )
}

function CommandItem({
  action,
  selected,
  onSelect,
}: {
  action: CommandAction
  selected: boolean
  onSelect: () => void
}) {
  return (
    <button
      onClick={onSelect}
      className={clsx(
        'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors',
        selected
          ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-900 dark:text-primary-100'
          : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
      )}
    >
      <span className={clsx(selected ? 'text-primary-600' : 'text-gray-400')}>
        {action.icon}
      </span>
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{action.title}</div>
        {action.subtitle && (
          <div className="text-sm text-gray-500 truncate">{action.subtitle}</div>
        )}
      </div>
      {action.shortcut && (
        <div className="flex items-center gap-1">
          {action.shortcut.map((key, i) => (
            <kbd
              key={i}
              className="px-1.5 py-0.5 text-xs bg-gray-100 dark:bg-gray-800 rounded"
            >
              {key}
            </kbd>
          ))}
        </div>
      )}
      {selected && <ArrowRight className="h-4 w-4 text-primary-500" />}
    </button>
  )
}

// Trigger button component
export function CommandPaletteTrigger({ className }: { className?: string }) {
  const { setOpen } = useCommandPalette()

  return (
    <button
      onClick={() => setOpen(true)}
      className={clsx(
        'flex items-center gap-2 px-3 py-1.5 text-sm text-gray-500 bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors',
        className
      )}
    >
      <Search className="h-4 w-4" />
      <span className="hidden md:inline">Search...</span>
      <kbd className="hidden md:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-xs bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
        ⌘K
      </kbd>
    </button>
  )
}
