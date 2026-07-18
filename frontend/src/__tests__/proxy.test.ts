/** @jest-environment node */

import { NextRequest } from 'next/server'

import { proxy } from '@/proxy'


describe('proxy', () => {
  it('redirects unauthenticated dashboard requests to login', () => {
    const response = proxy(
      new NextRequest('https://app.example.com/dashboard/settings')
    )

    expect(response.status).toBe(307)
    expect(response.headers.get('location')).toBe(
      'https://app.example.com/login?next=%2Fdashboard%2Fsettings'
    )
  })

  it('redirects authenticated users away from login', () => {
    const response = proxy(
      new NextRequest('https://app.example.com/login', {
        headers: { cookie: 'access_token=test-token' },
      })
    )

    expect(response.status).toBe(307)
    expect(response.headers.get('location')).toBe(
      'https://app.example.com/dashboard'
    )
  })

  it('adds a nonce-based content security policy to public routes', () => {
    const response = proxy(new NextRequest('https://app.example.com/'))
    const policy = response.headers.get('content-security-policy')

    expect(response.status).toBe(200)
    expect(policy).toContain("script-src 'self' 'nonce-")
    expect(policy).toContain("worker-src 'self' blob:")
    expect(policy).toContain("frame-ancestors 'none'")
  })
})
