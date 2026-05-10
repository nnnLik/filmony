import type { FeedListMode } from '../api/profileTypes'

export const FEED_SCROLL_STORAGE_KEY = 'filmony.feed.scrollRestore'

export type FeedScrollPayload = {
  mode: FeedListMode
  y: number
}

export function saveFeedScrollSnapshot(mode: FeedListMode, y: number): void {
  try {
    const payload: FeedScrollPayload = { mode, y }
    sessionStorage.setItem(FEED_SCROLL_STORAGE_KEY, JSON.stringify(payload))
  } catch {
    /* storage full / private mode */
  }
}

export function readFeedScrollSnapshot(): FeedScrollPayload | null {
  try {
    const raw = sessionStorage.getItem(FEED_SCROLL_STORAGE_KEY)
    if (raw == null || raw === '') return null
    const parsed: unknown = JSON.parse(raw)
    if (typeof parsed !== 'object' || parsed === null) return null
    if (!('mode' in parsed) || !('y' in parsed)) return null
    const mode = (parsed as { mode: unknown }).mode
    const y = (parsed as { y: unknown }).y
    if (typeof y !== 'number' || !Number.isFinite(y)) return null
    if (typeof mode !== 'string') return null
    return { mode: mode as FeedListMode, y }
  } catch {
    return null
  }
}
