'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { CheckCircle, Loader2, Shield, XCircle } from 'lucide-react';

import { authApi } from '@/lib/api';

type VerificationState = 'verifying' | 'verified' | 'failed';

export default function VerifyEmailPage() {
  const [state, setState] = useState<VerificationState>('verifying');

  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.slice(1));
    const token = params.get('token');
    window.history.replaceState(null, '', window.location.pathname);

    if (!token) {
      setState('failed');
      return;
    }

    authApi
      .verifyEmail(token)
      .then(() => setState('verified'))
      .catch(() => setState('failed'));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 text-center shadow-sm">
        <Shield className="mx-auto h-10 w-10 text-primary-600" />
        {state === 'verifying' ? (
          <>
            <Loader2 className="mx-auto mt-6 h-10 w-10 animate-spin text-primary-600" />
            <h1 className="mt-4 text-2xl font-bold text-gray-900">Verifying your email</h1>
          </>
        ) : state === 'verified' ? (
          <>
            <CheckCircle className="mx-auto mt-6 h-12 w-12 text-green-600" />
            <h1 className="mt-4 text-2xl font-bold text-gray-900">Email verified</h1>
            <p className="mt-2 text-gray-600">Your account is ready to use.</p>
            <Link href="/login" className="btn-primary mt-6 inline-flex">
              Sign in
            </Link>
          </>
        ) : (
          <>
            <XCircle className="mx-auto mt-6 h-12 w-12 text-red-600" />
            <h1 className="mt-4 text-2xl font-bold text-gray-900">Verification failed</h1>
            <p className="mt-2 text-gray-600">The verification link is invalid or has expired.</p>
            <Link href="/login" className="btn-secondary mt-6 inline-flex">
              Return to sign in
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
