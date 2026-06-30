import { afterEach, describe, expect, it, vi } from 'vitest'

import { getUserWatchlist, postCreateWatchlistEntry } from './profileApi'

describe('getUserWatchlist', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('returns normalized watchlist page from API', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          items: [
            {
              entry_id: 1,
              card_id: 'kp:123',
              provider: 'kinopoisk',
              title: 'Test Film',
              poster_url: 'https://example.com/p.jpg',
              year: 2024,
              watch_tag: 'watch_later',
              watch_with_user_id: null,
              created_at: '2026-06-30T12:00:00Z',
              film_id: 5,
              film_kinopoisk_id: 123,
              film_genres: ['драма'],
              catalog_item_id: null,
              external_id: '123',
            },
          ],
          next_cursor: null,
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await getUserWatchlist('user-1', { limit: 20 })

    expect(fetchMock).toHaveBeenCalledWith('/api/users/user-1/watchlist?limit=20', {
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
    expect(result.items[0]?.title).toBe('Test Film')
    expect(result.items[0]?.film_id).toBe(5)
  })
})

describe('postCreateWatchlistEntry', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('posts universal watchlist payload', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          entry_id: 2,
          card_id: 'rawg:elden-ring',
          provider: 'rawg',
          title: 'Elden Ring',
          poster_url: null,
          year: 2022,
          watch_tag: 'watch_later',
          watch_with_user_id: null,
          created_at: '2026-06-30T12:00:00Z',
          film_id: null,
          film_kinopoisk_id: null,
          film_genres: [],
          catalog_item_id: 9,
          external_id: 'elden-ring',
        }),
        {
          status: 201,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await postCreateWatchlistEntry({ catalog_item_id: 9 })

    expect(fetchMock).toHaveBeenCalledWith('/api/me/watchlist', {
      credentials: 'include',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify({ catalog_item_id: 9 }),
    })
    expect(result.provider).toBe('rawg')
    expect(result.catalog_item_id).toBe(9)
  })
})
