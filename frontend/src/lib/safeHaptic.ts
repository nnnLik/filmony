import { hapticFeedbackNotificationOccurred, isTMA } from '@telegram-apps/sdk'

/** Один короткий «успех» в Telegram Mini App; вне TMA или без поддержки — no-op */
export function safeHapticSuccess(): void {
  if (!isTMA()) {
    return
  }
  try {
    hapticFeedbackNotificationOccurred.ifAvailable('success')
  } catch {
    /* старый клиент / SDK не инициализирован */
  }
}
