function normalizeBotUsername(raw: string | undefined): string | null {
  const name = (raw ?? '').replace(/^\uFEFF/, '').trim().replace(/^@+/, '')
  return name === '' ? null : name
}

function encodeWatchlistCardIdForStartParam(cardId: string): string {
  const bytes = new TextEncoder().encode(cardId)
  let binary = ''
  for (const byte of bytes) {
    binary += String.fromCharCode(byte)
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function decodeWatchlistCardIdFromStartParam(encoded: string): string | null {
  try {
    const pad = encoded.length % 4 === 0 ? '' : '='.repeat(4 - (encoded.length % 4))
    const b64 = encoded.replace(/-/g, '+').replace(/_/g, '/') + pad
    const binary = atob(b64)
    const bytes = Uint8Array.from(binary, (ch) => ch.charCodeAt(0))
    return new TextDecoder().decode(bytes)
  } catch {
    return null
  }
}

/** Parses Telegram mini-app start_param for watchlist invite deeplinks (`w…` or `watchlist…`). */
export function parseMiniAppWatchlistStartParam(startParam: string): string | null {
  const sp = startParam.trim()
  if (sp === '') return null

  const compact = /^w([A-Za-z0-9_-]+)$/i.exec(sp)
  if (compact != null && compact[1] != null) {
    return decodeWatchlistCardIdFromStartParam(compact[1])
  }

  const prefixed = /^watchlist[-_]?(.+)$/i.exec(sp)
  if (prefixed != null && prefixed[1] != null) {
    const raw = prefixed[1]
    return decodeWatchlistCardIdFromStartParam(raw) ?? raw
  }

  return null
}

/** Parses Telegram mini-app start_param for film community deeplinks (`f…`). */
export function parseMiniAppFilmStartParam(startParam: string): number | null {
  const sp = startParam.trim()
  if (sp === '') return null
  const compact = /^f(\d+)$/i.exec(sp)
  if (compact == null || compact[1] == null) return null
  const filmId = Number(compact[1])
  if (!Number.isInteger(filmId) || filmId < 1) return null
  return filmId
}

export function buildMiniAppFilmDeepLink(filmId: number): string | null {
  if (!Number.isInteger(filmId) || filmId < 1) return null
  const bot = normalizeBotUsername(import.meta.env.VITE_TELEGRAM_BOT_USERNAME)
  if (bot == null) return null
  return `https://t.me/${bot}/app?startapp=f${filmId}`
}

export function buildMiniAppCardDeepLink(cardId: number): string | null {
  if (!Number.isInteger(cardId) || cardId < 1) return null
  const bot = normalizeBotUsername(import.meta.env.VITE_TELEGRAM_BOT_USERNAME)
  if (bot == null) return null
  return `https://t.me/${bot}/app?startapp=c${cardId}`
}

export function buildMiniAppWatchlistDeepLink(cardId: string): string | null {
  const trimmed = cardId.trim()
  if (trimmed === '') return null
  const bot = normalizeBotUsername(import.meta.env.VITE_TELEGRAM_BOT_USERNAME)
  if (bot == null) return null
  const encoded = encodeWatchlistCardIdForStartParam(trimmed)
  return `https://t.me/${bot}/app?startapp=w${encoded}`
}

/** Parses Telegram mini-app start_param for taste-quiz invite deeplinks (`tq…`). */
export function parseMiniAppTasteQuizStartParam(startParam: string): string | null {
  const sp = startParam.trim()
  if (sp === '') return null
  const compact = /^tq([A-Za-z0-9_-]+)$/i.exec(sp)
  if (compact != null && compact[1] != null && compact[1] !== '') {
    return compact[1]
  }
  return null
}

export function buildMiniAppTasteQuizDeepLink(inviteToken: string): string | null {
  const token = inviteToken.trim()
  if (token === '') return null
  const bot = normalizeBotUsername(import.meta.env.VITE_TELEGRAM_BOT_USERNAME)
  if (bot == null) return null
  return `https://t.me/${bot}/app?startapp=tq${token}`
}

/** Parses Telegram mini-app start_param for monthly recap deeplinks (`mr{year}-{month}` or legacy `r{year}{month}`). */
export function parseMiniAppRecapStartParam(startParam: string): { year: number; month: number } | null {
  const sp = startParam.trim()
  const modern = /^mr(\d{4})-(\d{1,2})$/i.exec(sp)
  if (modern != null) {
    const year = Number(modern[1])
    const month = Number(modern[2])
    if (Number.isInteger(year) && Number.isInteger(month) && month >= 1 && month <= 12) {
      return { year, month }
    }
  }
  const legacy = /^r(\d{4})(\d{1,2})$/i.exec(sp)
  if (legacy == null) return null
  const year = Number(legacy[1])
  const month = Number(legacy[2])
  if (!Number.isInteger(year) || !Number.isInteger(month) || month < 1 || month > 12) return null
  return { year, month }
}

export function buildMiniAppRecapDeepLink(year: number, month: number, botUsername: string): string {
  const bot = botUsername.trim().replace(/^@/, '')
  return `https://t.me/${bot}/app?startapp=mr${year}-${month}`
}

export const HANDLED_START_PARAM_KEY_PREFIX = 'filmony.handled_start_param.'

export function startParamHandledKey(startParam: string): string {
  return `${HANDLED_START_PARAM_KEY_PREFIX}${startParam}`
}

export function isStartParamHandled(startParam: string): boolean {
  return sessionStorage.getItem(startParamHandledKey(startParam)) === '1'
}

export function markStartParamHandled(startParam: string): void {
  sessionStorage.setItem(startParamHandledKey(startParam), '1')
}

/** Reads Telegram mini-app start_param synchronously (WebApp API or URL fallback). */
export function readTelegramStartParamSync(): string | undefined {
  const fromUnsafe = window.Telegram?.WebApp?.initDataUnsafe?.start_param?.trim()
  if (fromUnsafe) {
    return fromUnsafe
  }
  return new URLSearchParams(window.location.search).get('tgWebAppStartParam')?.trim() || undefined
}

export type StartParamRouteTarget = {
  path: string
  state?: unknown
}

/** Maps a Telegram start_param value to an in-app route (path + optional router state). */
export function resolveStartParamToPath(startParam: string): StartParamRouteTarget | null {
  const sp = startParam.trim()
  if (sp === '') {
    return null
  }

  const watchlistCardId = parseMiniAppWatchlistStartParam(sp)
  if (watchlistCardId != null) {
    return {
      path: '/profile?movies=watchlist',
      state: {
        watchlistInviteCardId: watchlistCardId,
      },
    }
  }

  const recapTarget = parseMiniAppRecapStartParam(sp)
  if (recapTarget != null) {
    return { path: `/me/recap/${recapTarget.year}/${recapTarget.month}` }
  }

  const tasteQuizToken = parseMiniAppTasteQuizStartParam(sp)
  if (tasteQuizToken != null) {
    return { path: `/taste-quiz/invite/${encodeURIComponent(tasteQuizToken)}` }
  }

  const filmId = parseMiniAppFilmStartParam(sp)
  if (filmId != null) {
    return { path: `/films/${filmId}` }
  }

  const cardMatch = /^c(\d+)$/i.exec(sp)
  if (cardMatch != null) {
    const cardId = Number(cardMatch[1])
    if (Number.isInteger(cardId) && cardId >= 1) {
      return {
        path: `/cards/${cardId}`,
        state: { cardEntry: 'telegram_start_param' as const },
      }
    }
  }

  const postMatch = /^p(\d+)$/i.exec(sp)
  if (postMatch != null) {
    const postId = Number(postMatch[1])
    if (Number.isInteger(postId) && postId >= 1) {
      return {
        path: `/feed-posts/${postId}`,
        state: { fromFeed: true },
      }
    }
  }

  return null
}

/** Returns unresolved start_param deeplink target, or null if absent/already handled. */
export function getPendingStartParamRedirect(): (StartParamRouteTarget & { startParam: string }) | null {
  const startParam = readTelegramStartParamSync()
  if (startParam == null || startParam === '') {
    return null
  }
  if (isStartParamHandled(startParam)) {
    return null
  }
  const resolved = resolveStartParamToPath(startParam)
  if (resolved == null) {
    return null
  }
  return { ...resolved, startParam }
}

/** Applies start_param path to the browser URL before React mounts (pathname + search only). */
export function applyEarlyStartParamPathReplace(): void {
  const pending = getPendingStartParamRedirect()
  if (pending == null) {
    return
  }
  const url = new URL(pending.path, window.location.origin)
  window.history.replaceState(window.history.state, '', `${url.pathname}${url.search}`)
}
