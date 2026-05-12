/** Пока нет id профиля в кэше — общий ключ для одного аккаунта в TMA на устройстве */
const FALLBACK_KEY = 'filmony.globalFeed.hideMine.v1'

const keyForUser = (userId: string) => `filmony.globalFeed.hideMine.v1.${userId}`

/** Читает флаг: сначала ключ с `userId`, иначе fallback (профиль ещё не подгрузился). */
export function readGlobalFeedHideMine(userId: string | null): boolean {
  try {
    if (userId != null && userId !== '') {
      if (window.localStorage.getItem(keyForUser(userId)) === '1') {
        return true
      }
    }
    return window.localStorage.getItem(FALLBACK_KEY) === '1'
  } catch {
    return false
  }
}

export function writeGlobalFeedHideMine(userId: string | null, hide: boolean): void {
  try {
    if (hide) {
      const k = userId != null && userId !== '' ? keyForUser(userId) : FALLBACK_KEY
      window.localStorage.setItem(k, '1')
      return
    }
    window.localStorage.removeItem(FALLBACK_KEY)
    if (userId != null && userId !== '') {
      window.localStorage.removeItem(keyForUser(userId))
    }
  } catch {
    /* ignore quota / private mode */
  }
}
