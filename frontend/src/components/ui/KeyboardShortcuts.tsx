'use client'

import * as React from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X, Keyboard } from 'lucide-react'

type ShortcutCategory = 'navigation' | 'actions' | 'general'

interface Shortcut {
  keys: string[]
  description: string
  category: ShortcutCategory
}

const shortcuts: Shortcut[] = [
  // Navigation
  { keys: ['⌘', 'K'], description: 'Open command palette', category: 'navigation' },
  { keys: ['G', 'D'], description: 'Go to Dashboard', category: 'navigation' },
  { keys: ['G', 'R'], description: 'Go to Regulations', category: 'navigation' },
  { keys: ['G', 'P'], description: 'Go to Repositories', category: 'navigation' },
  { keys: ['G', 'A'], description: 'Go to Actions', category: 'navigation' },
  { keys: ['G', 'U'], description: 'Go to Audit Trail', category: 'navigation' },
  { keys: ['G', 'S'], description: 'Go to Settings', category: 'navigation' },
  // Actions
  { keys: ['N', 'R'], description: 'New repository', category: 'actions' },
  { keys: ['N', 'S'], description: 'Run compliance scan', category: 'actions' },
  { keys: ['E', 'A'], description: 'Export audit report', category: 'actions' },
  { keys: ['⌘', 'Enter'], description: 'Submit / Confirm', category: 'actions' },
  // General
  { keys: ['?'], description: 'Show keyboard shortcuts', category: 'general' },
  { keys: ['Esc'], description: 'Close dialog / Cancel', category: 'general' },
  { keys: ['/'], description: 'Focus search', category: 'general' },
  { keys: ['⌘', 'D'], description: 'Toggle dark mode', category: 'general' },
]

interface KeyboardShortcutsContextValue {
  showShortcuts: () => void
  hideShortcuts: () => void
  registerShortcut: (keys: string[], callback: () => void) => () => void
}

const KeyboardShortcutsContext = React.createContext<KeyboardShortcutsContextValue | undefined>(
  undefined
)

export function useKeyboardShortcuts() {
  const context = React.useContext(KeyboardShortcutsContext)
  if (!context) {
    throw new Error('useKeyboardShortcuts must be used within a KeyboardShortcutsProvider')
  }
  return context
}

interface RegisteredShortcut {
  keys: string[]
  callback: () => void
}

export function KeyboardShortcutsProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false)
  const [registeredShortcuts, setRegisteredShortcuts] = React.useState<RegisteredShortcut[]>([])
  const pendingKeysRef = React.useRef<string[]>([])
  const timeoutRef = React.useRef<NodeJS.Timeout | null>(null)

  const showShortcuts = React.useCallback(() => setOpen(true), [])
  const hideShortcuts = React.useCallback(() => setOpen(false), [])

  const registerShortcut = React.useCallback((keys: string[], callback: () => void) => {
    const shortcut = { keys, callback }
    setRegisteredShortcuts((prev) => [...prev, shortcut])
    return () => {
      setRegisteredShortcuts((prev) => prev.filter((s) => s !== shortcut))
    }
  }, [])

  // Handle keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        (e.target as HTMLElement).isContentEditable
      ) {
        return
      }

      // Handle ? for shortcuts modal
      if (e.key === '?' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault()
        setOpen(true)
        return
      }

      // Handle / for focus search
      if (e.key === '/' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault()
        const searchInput = document.querySelector<HTMLInputElement>('[data-search-input]')
        searchInput?.focus()
        return
      }

      // Build key combination
      const key = e.key.toUpperCase()
      
      // Clear pending keys after timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      timeoutRef.current = setTimeout(() => {
        pendingKeysRef.current = []
      }, 1000)

      pendingKeysRef.current.push(key)
      const currentKeys = [...pendingKeysRef.current]

      // Check registered shortcuts
      for (const shortcut of registeredShortcuts) {
        const normalizedShortcutKeys = shortcut.keys.map((k) => k.toUpperCase())
        if (
          currentKeys.length === normalizedShortcutKeys.length &&
          currentKeys.every((k, i) => k === normalizedShortcutKeys[i])
        ) {
          e.preventDefault()
          pendingKeysRef.current = []
          shortcut.callback()
          return
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [registeredShortcuts])

  return (
    <KeyboardShortcutsContext.Provider value={{ showShortcuts, hideShortcuts, registerShortcut }}>
      {children}
      <ShortcutsDialog open={open} onOpenChange={setOpen} />
    </KeyboardShortcutsContext.Provider>
  )
}

function ShortcutsDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const categoryLabels: Record<ShortcutCategory, string> = {
    navigation: 'Navigation',
    actions: 'Actions',
    general: 'General',
  }

  const groupedShortcuts = React.useMemo(() => {
    return shortcuts.reduce((acc, shortcut) => {
      if (!acc[shortcut.category]) {
        acc[shortcut.category] = []
      }
      acc[shortcut.category].push(shortcut)
      return acc
    }, {} as Record<ShortcutCategory, Shortcut[]>)
  }, [])

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-white dark:bg-gray-900 rounded-xl shadow-2xl z-50 p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                <Keyboard className="h-5 w-5 text-primary-600" />
              </div>
              <Dialog.Title className="text-xl font-semibold text-gray-900 dark:text-white">
                Keyboard Shortcuts
              </Dialog.Title>
            </div>
            <Dialog.Close className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
              <X className="h-5 w-5" />
            </Dialog.Close>
          </div>

          <div className="space-y-6 max-h-[60vh] overflow-y-auto">
            {(Object.keys(groupedShortcuts) as ShortcutCategory[]).map((category) => (
              <div key={category}>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  {categoryLabels[category]}
                </h3>
                <div className="space-y-2">
                  {groupedShortcuts[category].map((shortcut, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
                    >
                      <span className="text-gray-700 dark:text-gray-300">{shortcut.description}</span>
                      <div className="flex items-center gap-1">
                        {shortcut.keys.map((key, j) => (
                          <React.Fragment key={j}>
                            {j > 0 && <span className="text-gray-400 mx-0.5">+</span>}
                            <kbd className="min-w-[24px] h-6 px-2 flex items-center justify-center text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded shadow-sm">
                              {key}
                            </kbd>
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 text-center">
              Press <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs">?</kbd> anywhere to show this dialog
            </p>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

// Hook for using navigation shortcuts
export function useNavigationShortcuts() {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const router = typeof window !== 'undefined' ? require('next/navigation').useRouter() : null
  const { registerShortcut } = useKeyboardShortcuts()

  React.useEffect(() => {
    if (!router) return

    const unregisters = [
      registerShortcut(['G', 'D'], () => router.push('/dashboard')),
      registerShortcut(['G', 'R'], () => router.push('/dashboard/regulations')),
      registerShortcut(['G', 'P'], () => router.push('/dashboard/repositories')),
      registerShortcut(['G', 'A'], () => router.push('/dashboard/actions')),
      registerShortcut(['G', 'U'], () => router.push('/dashboard/audit')),
      registerShortcut(['G', 'S'], () => router.push('/dashboard/settings')),
    ]

    return () => unregisters.forEach((unregister) => unregister())
  }, [router, registerShortcut])
}
