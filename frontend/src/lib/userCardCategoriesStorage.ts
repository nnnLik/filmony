import type { MyUserCardCategoryListResponse } from '../api/profileTypes'

/** Список полок меняется реже статистики тегов; достаточно суток для session placeholder. */
const CARD_CATEGORIES_STORAGE_MAX_AGE_MS = 24 * 60 * 60 * 1000

const KEY_MY = 'filmony-my-card-categories-v1'
const KEY_PUBLIC_PREFIX = 'filmony-public-card-categories-v1:'

type StoredBlob = {
  storedAt: number
  payload: MyUserCardCategoryListResponse
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
    if (Date.now() - parsed.storedAt > CARD_CATEGORIES_STORAGE_MAX_AGE_MS) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

export function readCachedMyCardCategories(): MyUserCardCategoryListResponse | null {
  try {
    const blob = parseBlob(sessionStorage.getItem(KEY_MY))
    return blob?.payload ?? null
  } catch {
    return null
  }
}

export function writeCachedMyCardCategories(data: MyUserCardCategoryListResponse): void {
  try {
    const blob: StoredBlob = { storedAt: Date.now(), payload: data }
    sessionStorage.setItem(KEY_MY, JSON.stringify(blob))
  } catch {
    /* ignore quota */
  }
}

export function readCachedPublicCardCategories(ownerUserId: string): MyUserCardCategoryListResponse | null {
  if (ownerUserId === '') {
    return null
  }
  try {
    const blob = parseBlob(sessionStorage.getItem(`${KEY_PUBLIC_PREFIX}${ownerUserId}`))
    return blob?.payload ?? null
  } catch {
    return null
  }
}

export function writeCachedPublicCardCategories(
  ownerUserId: string,
  data: MyUserCardCategoryListResponse,
): void {
  if (ownerUserId === '') {
    return
  }
  try {
    const blob: StoredBlob = { storedAt: Date.now(), payload: data }
    sessionStorage.setItem(`${KEY_PUBLIC_PREFIX}${ownerUserId}`, JSON.stringify(blob))
  } catch {
    /* ignore quota */
  }
}

/** Сброс при выходе / ошибке авторизации. */
export function clearUserCardCategoriesSessionCaches(): void {
  try {
    sessionStorage.removeItem(KEY_MY)
    const toRemove: string[] = []
    for (let i = 0; i < sessionStorage.length; i += 1) {
      const k = sessionStorage.key(i)
      if (k != null && k.startsWith(KEY_PUBLIC_PREFIX)) {
        toRemove.push(k)
      }
    }
    toRemove.forEach((k) => sessionStorage.removeItem(k))
  } catch {
    /* ignore */
  }
}
