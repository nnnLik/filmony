import type { GlobalFeedKind } from '../api/profileTypes'

export const FEED_SCROLL_STORAGE_KEY = 'filmony.feed.scrollRestore'

export type FeedScrollPayload = {
  kind: GlobalFeedKind
  y: number
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null
}

function modeToKind(mode: string): GlobalFeedKind | null {
  if (mode === 'default' || mode === 'subscriptions_only' || mode === 'subscribers_only') {
    return 'all'
  }
  if (mode === 'all' || mode === 'posts' || mode === 'cards') {
    return mode
  }
  return null
}

export function saveFeedScrollSnapshot(kind: GlobalFeedKind, y: number): void {
  try {
    const payload: FeedScrollPayload = { kind, y }
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
    if (!isRecord(parsed) || !('y' in parsed)) return null
    const y = parsed.y
    if (typeof y !== 'number' || !Number.isFinite(y)) return null

    if ('kind' in parsed) {
      const kind = parsed.kind
      if (kind === 'all' || kind === 'posts' || kind === 'cards') {
        return { kind, y }
      }
    }
    if ('mode' in parsed) {
      const mode = parsed.mode
      if (typeof mode === 'string') {
        const k = modeToKind(mode)
        if (k != null) {
          return { kind: k, y }
        }
      }
    }
    return null
  } catch {
    return null
  }
}
