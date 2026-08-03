import type { InfiniteData } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { FeedMovieCardPage } from '../api/feedListPageTypes'

const store = new Map<string, unknown>()

vi.mock('idb-keyval', () => ({
  get: vi.fn((key: string) => Promise.resolve(store.get(key))),
  set: vi.fn((key: string, value: unknown) => {
    store.set(key, value)
    return Promise.resolve()
  }),
  del: vi.fn((key: string) => {
    store.delete(key)
    return Promise.resolve()
  }),
  keys: vi.fn(() => Promise.resolve([...store.keys()])),
}))

import {
  GLOBAL_FEED_CACHE_MAX_AGE_MS,
  clearGlobalFeedCacheForUser,
  readCachedGlobalFeedPage,
  writeCachedGlobalFeedPage,
} from './globalFeedCacheStorage'

function sampleFeedData(): InfiniteData<FeedMovieCardPage, string | null> {
  return {
    pages: [
      {
        items: [],
        next_cursor: 'cursor-1',
        feed_head_version: 3,
      },
    ],
    pageParams: [null],
  }
}

describe('globalFeedCacheStorage', () => {
  beforeEach(() => {
    store.clear()
    vi.clearAllMocks()
  })

  it('writes and reads first page only', async () => {
    await writeCachedGlobalFeedPage('user-1', 'all', false, {
      pages: [
        { items: [], next_cursor: 'a', feed_head_version: 1 },
        { items: [], next_cursor: 'b', feed_head_version: 1 },
      ],
      pageParams: [null, 'a'],
    })

    const blob = await readCachedGlobalFeedPage('user-1', 'all', false)
    expect(blob).not.toBeNull()
    expect(blob?.payload.pages).toHaveLength(1)
    expect(blob?.payload.pages[0]?.next_cursor).toBe('a')
    expect(blob?.payload.pageParams).toEqual([null])
  })

  it('scopes cache by kind and excludeOwn', async () => {
    await writeCachedGlobalFeedPage('user-1', 'all', false, sampleFeedData())
    await writeCachedGlobalFeedPage('user-1', 'posts', true, sampleFeedData())

    const allBlob = await readCachedGlobalFeedPage('user-1', 'all', false)
    const postsBlob = await readCachedGlobalFeedPage('user-1', 'posts', true)
    const missing = await readCachedGlobalFeedPage('user-1', 'all', true)

    expect(allBlob).not.toBeNull()
    expect(postsBlob).not.toBeNull()
    expect(missing).toBeNull()
  })

  it('expires stale blobs', async () => {
    await writeCachedGlobalFeedPage('user-1', 'all', false, sampleFeedData())
    const key = 'filmony.globalFeed.v1:user-1:all:0'
    const raw = store.get(key) as { storedAt: number }
    raw.storedAt = Date.now() - GLOBAL_FEED_CACHE_MAX_AGE_MS - 1
    store.set(key, raw)

    const blob = await readCachedGlobalFeedPage('user-1', 'all', false)
    expect(blob).toBeNull()
    expect(store.has(key)).toBe(false)
  })

  it('clears cache for one user', async () => {
    await writeCachedGlobalFeedPage('user-1', 'all', false, sampleFeedData())
    await writeCachedGlobalFeedPage('user-2', 'all', false, sampleFeedData())

    await clearGlobalFeedCacheForUser('user-1')

    expect(await readCachedGlobalFeedPage('user-1', 'all', false)).toBeNull()
    expect(await readCachedGlobalFeedPage('user-2', 'all', false)).not.toBeNull()
  })
})
