import { resolveApiUrl } from '../api/client'

/** Absolute URL for a movie-card comment image (API path or absolute). */
export function movieCardCommentImageSrc(url: string): string {
  const u = url.trim()
  if (u.startsWith('http://') || u.startsWith('https://')) return u
  return resolveApiUrl(u.startsWith('/') ? u : `/${u}`)
}
