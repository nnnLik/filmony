/** Полный URL публичного профиля в этом origin (мини-приложение / веб). */
export function publicProfilePageUrl(slug: string): string {
  const s = slug.trim()
  const origin = typeof window !== 'undefined' ? window.location.origin.replace(/\/$/, '') : ''
  return `${origin}/u/${encodeURIComponent(s)}`
}
