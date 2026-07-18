import { resolveApiBaseUrl } from '@/lib/config'

describe('resolveApiBaseUrl', () => {
  it('returns localhost default when unset in development', () => {
    expect(resolveApiBaseUrl(undefined, 'development')).toBe('http://localhost:8000')
  })

  it('throws in production when unset', () => {
    expect(() => resolveApiBaseUrl(undefined, 'production')).toThrow(
      /must be set in production/
    )
  })

  it('throws in production when pointing at localhost', () => {
    expect(() => resolveApiBaseUrl('http://localhost:8000', 'production')).toThrow(
      /must not point at localhost/
    )
    expect(() => resolveApiBaseUrl('http://127.0.0.1:8000', 'production')).toThrow(
      /must not point at localhost/
    )
  })

  it('accepts an explicit same-origin production deployment', () => {
    expect(resolveApiBaseUrl('same-origin', 'production')).toBe('')
  })

  it('rejects non-TLS remote origins in production', () => {
    expect(() =>
      resolveApiBaseUrl('http://api.example.com', 'production')
    ).toThrow(/must use HTTPS/)
  })

  it('throws on an invalid URL', () => {
    expect(() => resolveApiBaseUrl('not a url', 'production')).toThrow(/not a valid URL/)
  })

  it('accepts a valid production origin and strips trailing slashes', () => {
    expect(resolveApiBaseUrl('https://api.example.com/', 'production')).toBe(
      'https://api.example.com'
    )
    expect(resolveApiBaseUrl('https://api.example.com', 'production')).toBe(
      'https://api.example.com'
    )
  })

  it('allows localhost in development', () => {
    expect(resolveApiBaseUrl('http://localhost:8000', 'development')).toBe(
      'http://localhost:8000'
    )
  })
})
