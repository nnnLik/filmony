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
