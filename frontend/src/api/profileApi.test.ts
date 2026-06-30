import { afterEach, describe, expect, it, vi } from 'vitest'

import { getUserWatchlist } from './profileApi'

describe('getUserWatchlist', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('returns empty page when API responds 404', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Not Found' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await getUserWatchlist('user-1', { limit: 20 })

    expect(fetchMock).toHaveBeenCalledWith('/api/users/user-1/watchlist?limit=20', {
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
    expect(result).toEqual({ items: [], next_cursor: null })
  })
})
