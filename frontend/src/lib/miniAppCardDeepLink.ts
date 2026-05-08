function normalizeBotUsername(raw: string | undefined): string | null {
  const name = (raw ?? '').replace(/^\uFEFF/, '').trim().replace(/^@+/, '')
  return name === '' ? null : name
}

export function buildMiniAppCardDeepLink(cardId: number): string | null {
  if (!Number.isInteger(cardId) || cardId < 1) return null
  const bot = normalizeBotUsername(import.meta.env.VITE_TELEGRAM_BOT_USERNAME)
  if (bot == null) return null
  return `https://t.me/${bot}/app?startapp=c${cardId}`
}
