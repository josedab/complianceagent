'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ThemeProvider } from '@/components/ThemeToggle'
import { ToastProvider } from '@/components/ui/Toast'
import { CommandPaletteProvider } from '@/components/ui/CommandPalette'
import { KeyboardShortcutsProvider } from '@/components/ui/KeyboardShortcuts'
import { OnboardingProvider } from '@/components/ui/OnboardingTour'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastProvider>
          <KeyboardShortcutsProvider>
            <CommandPaletteProvider>
              <OnboardingProvider>
                <ErrorBoundary>
                  {children}
                </ErrorBoundary>
              </OnboardingProvider>
            </CommandPaletteProvider>
          </KeyboardShortcutsProvider>
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
