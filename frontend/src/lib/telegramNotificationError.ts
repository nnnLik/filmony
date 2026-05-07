import { formatApiDetail } from '../api/client'

export type TelegramChatUnavailableDetail = {
  code: 'telegram_chat_unavailable'
  message: string
  bot_username?: string | null
}

export function isTelegramChatUnavailableDetail(detail: unknown): detail is TelegramChatUnavailableDetail {
  if (detail === null || typeof detail !== 'object' || Array.isArray(detail)) {
    return false
  }
  const d = detail as Record<string, unknown>
  return d.code === 'telegram_chat_unavailable' && typeof d.message === 'string'
}

export function openTelegramDeepLink(url: string): void {
  const wa = window.Telegram?.WebApp
  if (wa?.openTelegramLink) {
    wa.openTelegramLink(url)
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

/** Prefer server `message` for structured errors (e.g. `telegram_delivery_failed`). */
export function notificationFailureMessage(detail: unknown): string {
  if (detail !== null && typeof detail === 'object' && !Array.isArray(detail)) {
    const d = detail as Record<string, unknown>
    if (typeof d.message === 'string' && d.message.trim() !== '') {
      return d.message
    }
  }
  return formatApiDetail(detail)
}

export function telegramBotOpenUrl(botUsername: string | null | undefined): string | null {
  if (botUsername == null || String(botUsername).trim() === '') {
    return null
  }
  const name = String(botUsername).replace(/^@/, '')
  if (!name) {
    return null
  }
  return `https://t.me/${name}`
}
