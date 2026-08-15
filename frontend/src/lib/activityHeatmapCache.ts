import type { UserActivityHeatmap } from '../api/profileTypes'

const KEY_PREFIX = 'filmony-activity-heatmap-v1:'
const MAX_AGE_MS = 5 * 60 * 1000

type StoredBlob = {
  storedAt: number
  payload: UserActivityHeatmap
}

function isValidPayload(payload: unknown): payload is UserActivityHeatmap {
  if (payload == null || typeof payload !== 'object') {
    return false
  }
  const p = payload as UserActivityHeatmap
  return (
    Array.isArray(p.activity_distribution) &&
    Array.isArray(p.category_distribution) &&
    typeof p.activity_start === 'string' &&
    typeof p.activity_end === 'string'
  )
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
      !isValidPayload(parsed.payload)
    ) {
      return null
    }
    if (Date.now() - parsed.storedAt > MAX_AGE_MS) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function readCachedUserActivityHeatmap(userId: string): UserActivityHeatmap | null {
  if (userId === '') {
    return null
  }
  try {
    const blob = parseBlob(sessionStorage.getItem(`${KEY_PREFIX}${userId}`))
    return blob?.payload ?? null
  } catch {
    return null
  }
}

export function writeCachedUserActivityHeatmap(userId: string, data: UserActivityHeatmap): void {
  if (userId === '') {
    return
  }
  try {
    const blob: StoredBlob = { storedAt: Date.now(), payload: data }
    sessionStorage.setItem(`${KEY_PREFIX}${userId}`, JSON.stringify(blob))
  } catch {
    /* ignore quota */
  }
}

/** Сброс при выходе / ошибке авторизации. */
export function clearActivityHeatmapSessionCaches(): void {
  try {
    const toRemove: string[] = []
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const k = sessionStorage.key(i)
      if (k != null && k.startsWith(KEY_PREFIX)) {
        toRemove.push(k)
      }
    }
    toRemove.forEach((k) => sessionStorage.removeItem(k))
  } catch {
    /* ignore */
  }
}
