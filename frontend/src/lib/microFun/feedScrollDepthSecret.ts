export const FEED_SCROLL_SECRET_BOTTOM_THRESHOLD_PX = 48
export const FEED_SCROLL_SECRET_HITS_TO_TRIGGER = 3
export const FEED_SCROLL_SECRET_STORAGE_PREFIX = 'filmony.feed-scroll-secret.v1'

export type FeedScrollSecretSessionState = {
  bottomHits: number
  triggered: boolean
}

export function feedScrollSecretStorageKey(userId: string | number): string {
  return `${FEED_SCROLL_SECRET_STORAGE_PREFIX}:${String(userId)}`
}

export function isScrollAtBottom(
  scrollTop: number,
  clientHeight: number,
  scrollHeight: number,
  thresholdPx: number = FEED_SCROLL_SECRET_BOTTOM_THRESHOLD_PX,
): boolean {
  if (scrollHeight <= 0) {
    return false
  }
  return scrollTop + clientHeight >= scrollHeight - thresholdPx
}

export function parseFeedScrollSecretSession(raw: string | null): FeedScrollSecretSessionState {
  if (raw == null || raw.trim() === '') {
    return { bottomHits: 0, triggered: false }
  }
  try {
    const parsed: unknown = JSON.parse(raw)
    if (typeof parsed !== 'object' || parsed == null) {
      return { bottomHits: 0, triggered: false }
    }
    const record = parsed as Record<string, unknown>
    const bottomHits =
      typeof record.bottomHits === 'number' && Number.isFinite(record.bottomHits)
        ? Math.max(0, Math.floor(record.bottomHits))
        : 0
    const triggered = record.triggered === true
    return { bottomHits, triggered }
  } catch {
    return { bottomHits: 0, triggered: false }
  }
}

export function serializeFeedScrollSecretSession(state: FeedScrollSecretSessionState): string {
  return JSON.stringify(state)
}

export type FeedScrollBottomEdgeResult = {
  nextState: FeedScrollSecretSessionState
  shouldTrigger: boolean
}

/**
 * Edge-trigger: counts a bottom hit only when transitioning from not-at-bottom to at-bottom.
 */
export function onFeedScrollBottomEdge({
  wasAtBottom,
  isAtBottom,
  session,
}: {
  wasAtBottom: boolean
  isAtBottom: boolean
  session: FeedScrollSecretSessionState
}): FeedScrollBottomEdgeResult {
  if (session.triggered) {
    return { nextState: session, shouldTrigger: false }
  }
  if (!isAtBottom || wasAtBottom) {
    return { nextState: session, shouldTrigger: false }
  }

  const bottomHits = session.bottomHits + 1
  if (bottomHits >= FEED_SCROLL_SECRET_HITS_TO_TRIGGER) {
    return {
      nextState: { bottomHits, triggered: true },
      shouldTrigger: true,
    }
  }
  return {
    nextState: { ...session, bottomHits },
    shouldTrigger: false,
  }
}
