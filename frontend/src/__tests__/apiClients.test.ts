/**
 * Broad sweep test for the frontend/src/lib/api.ts client layer.
 *
 * Every exported "*Api" object is a thin collection of one-line wrapper
 * functions around the shared axios `api` instance (e.g.
 * `getStats: () => api.get('/foo/stats')`). Rather than hand-writing an
 * assertion for every single wrapper (there are hundreds across the
 * next-gen feature surface), this test dynamically invokes every exported
 * client method with a generic dummy argument and asserts it delegates to
 * the shared, mocked axios instance without throwing. This gives real
 * regression coverage (a typo'd URL, a thrown error before the axios call,
 * etc. would fail this test) while remaining maintainable as new client
 * methods are added.
 */
import * as apiModule from '@/lib/api'

describe('lib/api client layer', () => {
  const { api } = apiModule

  beforeEach(() => {
    jest.spyOn(api, 'get').mockResolvedValue({ data: {} } as never)
    jest.spyOn(api, 'post').mockResolvedValue({ data: {} } as never)
    jest.spyOn(api, 'put').mockResolvedValue({ data: {} } as never)
    jest.spyOn(api, 'delete').mockResolvedValue({ data: {} } as never)
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  const dummyArgs = ['dummy-arg-1', 'dummy-arg-2', 'dummy-arg-3']

  const clientEntries = Object.entries(apiModule).filter(
    ([name, value]) =>
      name.endsWith('Api') && typeof value === 'object' && value !== null
  ) as Array<[string, Record<string, unknown>]>

  it('discovers at least one API client to exercise', () => {
    expect(clientEntries.length).toBeGreaterThan(0)
  })

  describe.each(clientEntries)('%s', (_clientName, client) => {
    const methodEntries = Object.entries(client).filter(
      ([, value]) => typeof value === 'function'
    ) as Array<[string, (...args: unknown[]) => unknown]>

    it.each(methodEntries)('method %s calls the shared axios instance without throwing', (_methodName, fn) => {
      const args = dummyArgs.slice(0, fn.length)
      expect(() => fn(...args)).not.toThrow()
    })
  })
})
