/** Полный URL публичного профиля в этом origin (мини-приложение / веб). */
export function publicProfilePageUrl(userId: string): string {
  const s = userId.trim()
  const origin = typeof window !== 'undefined' ? window.location.origin.replace(/\/$/, '') : ''
  return `${origin}/u/${encodeURIComponent(s)}`
}
