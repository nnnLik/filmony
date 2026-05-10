import type { MyMovieCardTagStatsResponse } from '../api/profileTypes'

/** Дольше, чем bundle профиля: подсказки тегов редко «портятся» от устаревания. */
const TAG_STATS_STORAGE_MAX_AGE_MS = 24 * 60 * 60 * 1000

const KEY_ME = 'filmony-movie-card-tag-stats-me-v1'
const KEY_USER_PREFIX = 'filmony-movie-card-tag-stats-u-v1:'

type StoredBlob = {
  storedAt: number
  payload: MyMovieCardTagStatsResponse
}

function parseBlob(raw: string | null): StoredBlob | null {
  if (raw == null || raw === '') {
    return null
  }
  try {
    const parsed = JSON.parse(raw) as StoredBlob
    if (
      parsed == null ||
      typeof parsed.storedAt !== 'number' ||
      parsed.payload == null ||
      !Array.isArray(parsed.payload.items)
    ) {
      return null
    }
    if (Date.now() - parsed.storedAt > TAG_STATS_STORAGE_MAX_AGE_MS) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function readCachedMyMovieCardTagStats(): MyMovieCardTagStatsResponse | null {
  try {
    const blob = parseBlob(sessionStorage.getItem(KEY_ME))
    return blob?.payload ?? null
  } catch {
    return null
  }
}

export function writeCachedMyMovieCardTagStats(data: MyMovieCardTagStatsResponse): void {
  try {
    const blob: StoredBlob = { storedAt: Date.now(), payload: data }
    sessionStorage.setItem(KEY_ME, JSON.stringify(blob))
  } catch {
    /* ignore quota */
  }
}

export function readCachedUserMovieCardTagStats(userId: string): MyMovieCardTagStatsResponse | null {
  if (userId === '') {
    return null
  }
  try {
    const blob = parseBlob(sessionStorage.getItem(`${KEY_USER_PREFIX}${userId}`))
    return blob?.payload ?? null
  } catch {
    return null
  }
}

export function writeCachedUserMovieCardTagStats(userId: string, data: MyMovieCardTagStatsResponse): void {
  if (userId === '') {
    return
  }
  try {
    const blob: StoredBlob = { storedAt: Date.now(), payload: data }
    sessionStorage.setItem(`${KEY_USER_PREFIX}${userId}`, JSON.stringify(blob))
  } catch {
    /* ignore */
  }
}

/** Сброс при выходе / ошибке авторизации (не вызывать из clearMyProfileBundleCache). */
export function clearMovieCardTagStatsSessionCaches(): void {
  try {
    sessionStorage.removeItem(KEY_ME)
    const toRemove: string[] = []
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const k = sessionStorage.key(i)
      if (k != null && k.startsWith(KEY_USER_PREFIX)) {
        toRemove.push(k)
      }
    }
    toRemove.forEach((k) => sessionStorage.removeItem(k))
  } catch {
    /* ignore */
  }
}
