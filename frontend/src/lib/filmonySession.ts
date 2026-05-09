/** Ключ sessionStorage: после успешного POST /api/auth/telegram в этой вкладке */
export const AUTH_SESSION_STORAGE_KEY = 'filmony_tma_authenticated_v1'

const ACCESS_TOKEN_STORAGE_KEY = 'filmony_access_token_v1'

export function readAccessToken(): string | null {
  try {
    const v = sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)
    return v && v.trim() ? v.trim() : null
  } catch {
    return null
  }
}

export function writeAccessToken(token: string | null): void {
  try {
    if (token && token.trim()) {
      sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token.trim())
    } else {
      sessionStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY)
    }
  } catch {
    /* private mode */
  }
}

/** Кеш ответа «мой профиль + карточки» для мгновенного показа при возврате на экран */
export const MY_PROFILE_BUNDLE_STORAGE_KEY = 'filmony_me_profile_bundle_v1'

export const MY_PROFILE_CACHE_MAX_AGE_MS = 12 * 60 * 1000

export function readAuthSessionFlag(): boolean {
  try {
    return sessionStorage.getItem(AUTH_SESSION_STORAGE_KEY) === '1'
  } catch {
    return false
  }
}

export function writeAuthSessionFlag(ok: boolean): void {
  try {
    if (ok) {
      sessionStorage.setItem(AUTH_SESSION_STORAGE_KEY, '1')
    } else {
      sessionStorage.removeItem(AUTH_SESSION_STORAGE_KEY)
      sessionStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY)
    }
  } catch {
    /* private mode / quota */
  }
}
