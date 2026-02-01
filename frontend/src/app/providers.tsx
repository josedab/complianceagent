'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ThemeProvider } from '@/components/ThemeToggle'

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
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
