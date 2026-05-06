/** Дополняет относительные API-пути полным origin (картинки реакций `/api/reactions/asset/...`). */
export function resolveApiMediaUrl(url: string): string {
  const u = url.trim()
  if (!u.startsWith('/api/')) {
    return u
  }
  const baseRaw = import.meta.env.VITE_API_ORIGIN
  const base = (typeof baseRaw === 'string' ? baseRaw : '').replace(/\/$/, '')
  return base ? `${base}${u}` : u
}
