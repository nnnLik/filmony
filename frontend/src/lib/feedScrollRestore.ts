import type { GlobalFeedKind } from '../api/profileTypes'

export const FEED_SCROLL_STORAGE_KEY = 'filmony.feed.scrollRestore'

export type FeedScrollPayload = {
  kind: GlobalFeedKind
  y: number
}

function clearLegacyScrollSnapshot(): void {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.removeItem(FEED_SCROLL_STORAGE_KEY)
  } catch (error) {
    void error
  }
}

export function saveFeedScrollSnapshot(kind: GlobalFeedKind, y: number): void {
  void kind
  void y
  // Global scroll restore provider handles storage now.
  clearLegacyScrollSnapshot()
}

export function readFeedScrollSnapshot(): FeedScrollPayload | null {
  clearLegacyScrollSnapshot()
  return null
}
