import { openTelegramDeepLink } from './telegramNotificationError'

export function openTelegramShareUrl(url: string, text: string): void {
  const share = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`
  openTelegramDeepLink(share)
}
