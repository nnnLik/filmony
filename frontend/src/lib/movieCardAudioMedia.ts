import { resolveApiUrl } from '../api/client'

/**
 * Задержка перед стартом воспроизведения после нажатия «play» (мс).
 * Не настраивается в UI — только константа для возможной тонкой подстройки UX.
 */
export const MOVIE_CARD_AUDIO_PLAY_START_DELAY_MS = 0

/** Absolute URL for card vibe audio (API proxy path or absolute). */
export function movieCardAudioSrc(url: string): string {
  const u = url.trim()
  if (u.startsWith('http://') || u.startsWith('https://')) return u
  return resolveApiUrl(u.startsWith('/') ? u : `/${u}`)
}
