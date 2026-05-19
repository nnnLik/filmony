import { resolveApiUrl } from '../api/client'

/** Absolute URL for card vibe audio (API proxy path or absolute). */
export function movieCardAudioSrc(url: string): string {
  const u = url.trim()
  if (u.startsWith('http://') || u.startsWith('https://')) return u
  return resolveApiUrl(u.startsWith('/') ? u : `/${u}`)
}
