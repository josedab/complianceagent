'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authApi, organizationsApi } from '@/lib/api';

interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  organization_id?: string | null;
  avatar_url?: string | null;
  mfa_enabled?: boolean;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
  mfaRequired: boolean;
  mfaToken: string | null;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  completeMfa: (totpCode: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
    mfaRequired: false,
    mfaToken: null,
  });

  const fetchUser = useCallback(async () => {
    try {
      const res = await authApi.me();
      let invitationError: string | null = null;
      if (typeof window !== 'undefined') {
        const invitationToken = window.sessionStorage.getItem('pending_invitation_token');
        if (invitationToken) {
          try {
            const accepted = await organizationsApi.acceptInvitation(invitationToken);
            await authApi.switchOrganization(accepted.data.organization_id);
          } catch {
            invitationError = 'The organization invitation could not be accepted.';
          } finally {
            window.sessionStorage.removeItem('pending_invitation_token');
          }
        }
      }
      setState({
        user: res.data,
        loading: false,
        error: invitationError,
        mfaRequired: false,
        mfaToken: null,
      });
    } catch {
      setState({ user: null, loading: false, error: null, mfaRequired: false, mfaToken: null });
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        const res = await authApi.login(email, password);
        if (res.data.token_type === 'mfa_required') {
          setState((s) => ({
            ...s,
            loading: false,
            mfaRequired: true,
            mfaToken: res.data.mfa_token,
          }));
          return;
        }
        await fetchUser();
        router.push('/dashboard');
      } catch (err: unknown) {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          'Login failed';
        setState((s) => ({ ...s, loading: false, error: message }));
        throw err;
      }
    },
    [fetchUser, router]
  );

  const completeMfa = useCallback(
    async (totpCode: string) => {
      if (!state.mfaToken) throw new Error('No MFA token');
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        await authApi.mfaChallenge(state.mfaToken, totpCode);
        await fetchUser();
        router.push('/dashboard');
      } catch (err: unknown) {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          'Invalid code';
        setState((s) => ({ ...s, loading: false, error: message }));
        throw err;
      }
    },
    [fetchUser, router, state.mfaToken]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore errors — clear state regardless
    }
    setState({ user: null, loading: false, error: null, mfaRequired: false, mfaToken: null });
    router.push('/login');
  }, [router]);

  const refresh = useCallback(async () => {
    await fetchUser();
  }, [fetchUser]);

  const value = useMemo<AuthContextValue>(
    () => ({ ...state, login, logout, refresh, completeMfa }),
    [state, login, logout, refresh, completeMfa]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
