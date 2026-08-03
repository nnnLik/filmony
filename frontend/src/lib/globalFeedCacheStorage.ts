import type { InfiniteData } from '@tanstack/react-query'
import { del, get, keys, set } from 'idb-keyval'

import type { FeedMovieCardPage } from '../api/feedListPageTypes'
import type { GlobalFeedKind } from '../api/profileTypes'

/** Дольше staleTime ленты: offline snapshot для первого экрана при плохой сети. */
export const GLOBAL_FEED_CACHE_MAX_AGE_MS = 24 * 60 * 60 * 1000

const KEY_PREFIX = 'filmony.globalFeed.v1:'

export type GlobalFeedCacheBlob = {
  storedAt: number
  payload: InfiniteData<FeedMovieCardPage, string | null>
}

function cacheKey(userId: string, kind: GlobalFeedKind, excludeOwn: boolean): string {
  return `${KEY_PREFIX}${userId}:${kind}:${excludeOwn ? '1' : '0'}`
}

function isValidBlob(value: unknown): value is GlobalFeedCacheBlob {
  if (value == null || typeof value !== 'object') {
    return false
  }
  const row = value as GlobalFeedCacheBlob
  if (typeof row.storedAt !== 'number' || row.payload == null) {
    return false
  }
  if (!Array.isArray(row.payload.pages) || !Array.isArray(row.payload.pageParams)) {
    return false
  }
  return row.payload.pages.every(
    (page) =>
      page != null &&
      typeof page === 'object' &&
      Array.isArray(page.items),
  )
}

function firstPageOnly(
  data: InfiniteData<FeedMovieCardPage, string | null>,
): InfiniteData<FeedMovieCardPage, string | null> {
  const firstPage = data.pages[0]
  if (firstPage == null) {
    return { pages: [], pageParams: [] }
  }
  return {
    pages: [firstPage],
    pageParams: [data.pageParams[0] ?? null],
  }
}

export async function readCachedGlobalFeedPage(
  userId: string,
  kind: GlobalFeedKind,
  excludeOwn: boolean,
): Promise<GlobalFeedCacheBlob | null> {
  if (userId === '') {
    return null
  }
  try {
    const raw = await get<unknown>(cacheKey(userId, kind, excludeOwn))
    if (!isValidBlob(raw)) {
      return null
    }
    if (Date.now() - raw.storedAt > GLOBAL_FEED_CACHE_MAX_AGE_MS) {
      await del(cacheKey(userId, kind, excludeOwn))
      return null
    }
    return {
      storedAt: raw.storedAt,
      payload: firstPageOnly(raw.payload),
    }
  } catch {
    return null
  }
}

export async function writeCachedGlobalFeedPage(
  userId: string,
  kind: GlobalFeedKind,
  excludeOwn: boolean,
  data: InfiniteData<FeedMovieCardPage, string | null>,
): Promise<void> {
  if (userId === '' || data.pages[0] == null) {
    return
  }
  try {
    const blob: GlobalFeedCacheBlob = {
      storedAt: Date.now(),
      payload: firstPageOnly(data),
    }
    await set(cacheKey(userId, kind, excludeOwn), blob)
  } catch {
    /* quota / private mode */
  }
}

export async function clearGlobalFeedCacheForUser(userId: string): Promise<void> {
  if (userId === '') {
    return
  }
  try {
    const prefix = `${KEY_PREFIX}${userId}:`
    const allKeys = await keys()
    const toDelete = allKeys.filter(
      (key) => typeof key === 'string' && key.startsWith(prefix),
    )
    await Promise.all(toDelete.map((key) => del(key)))
  } catch {
    /* ignore */
  }
}

export async function clearGlobalFeedCache(): Promise<void> {
  try {
    const allKeys = await keys()
    const toDelete = allKeys.filter(
      (key) => typeof key === 'string' && key.startsWith(KEY_PREFIX),
    )
    await Promise.all(toDelete.map((key) => del(key)))
  } catch {
    /* ignore */
  }
}
