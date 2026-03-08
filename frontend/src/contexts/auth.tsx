'use client'

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { useRouter } from 'next/navigation'
import { authApi } from '@/lib/api'

interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  organization_id?: string | null
}

interface AuthState {
  user: User | null
  loading: boolean
  error: string | null
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  })

  const fetchUser = useCallback(async () => {
    try {
      const res = await authApi.me()
      setState({ user: res.data, loading: false, error: null })
    } catch {
      setState({ user: null, loading: false, error: null })
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const login = useCallback(
    async (email: string, password: string) => {
      setState((s) => ({ ...s, loading: true, error: null }))
      try {
        await authApi.login(email, password)
        await fetchUser()
        router.push('/dashboard')
      } catch (err: unknown) {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response?.data
            ?.detail || 'Login failed'
        setState((s) => ({ ...s, loading: false, error: message }))
        throw err
      }
    },
    [fetchUser, router]
  )

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      // Ignore errors — clear state regardless
    }
    setState({ user: null, loading: false, error: null })
    router.push('/login')
  }, [router])

  const refresh = useCallback(async () => {
    await fetchUser()
  }, [fetchUser])

  const value = useMemo<AuthContextValue>(
    () => ({ ...state, login, logout, refresh }),
    [state, login, logout, refresh]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
