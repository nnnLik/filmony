import { describe, expect, it } from 'vitest'

import {
  FEED_SCROLL_SECRET_HITS_TO_TRIGGER,
  isScrollAtBottom,
  onFeedScrollBottomEdge,
  parseFeedScrollSecretSession,
  serializeFeedScrollSecretSession,
} from '../feedScrollDepthSecret'

describe('isScrollAtBottom', () => {
  it('detects bottom within threshold', () => {
    expect(isScrollAtBottom(952, 600, 1000, 48)).toBe(true)
    expect(isScrollAtBottom(300, 600, 1000, 48)).toBe(false)
  })

  it('returns false for zero scroll height', () => {
    expect(isScrollAtBottom(0, 600, 0)).toBe(false)
  })
})

describe('onFeedScrollBottomEdge', () => {
  it('increments only on false-to-true transition', () => {
    const first = onFeedScrollBottomEdge({
      wasAtBottom: false,
      isAtBottom: true,
      session: { bottomHits: 0, triggered: false },
    })
    expect(first.nextState.bottomHits).toBe(1)
    expect(first.shouldTrigger).toBe(false)

    const stay = onFeedScrollBottomEdge({
      wasAtBottom: true,
      isAtBottom: true,
      session: first.nextState,
    })
    expect(stay.nextState.bottomHits).toBe(1)
    expect(stay.shouldTrigger).toBe(false)
  })

  it('triggers on third bottom hit', () => {
    let session = { bottomHits: 0, triggered: false }
    for (let i = 0; i < FEED_SCROLL_SECRET_HITS_TO_TRIGGER - 1; i += 1) {
      const result = onFeedScrollBottomEdge({
        wasAtBottom: false,
        isAtBottom: true,
        session,
      })
      session = result.nextState
      expect(result.shouldTrigger).toBe(false)
    }
    const final = onFeedScrollBottomEdge({
      wasAtBottom: false,
      isAtBottom: true,
      session,
    })
    expect(final.shouldTrigger).toBe(true)
    expect(final.nextState.triggered).toBe(true)
  })

  it('does not increment after triggered', () => {
    const result = onFeedScrollBottomEdge({
      wasAtBottom: false,
      isAtBottom: true,
      session: { bottomHits: 3, triggered: true },
    })
    expect(result.shouldTrigger).toBe(false)
    expect(result.nextState.bottomHits).toBe(3)
  })
})

describe('session storage helpers', () => {
  it('round-trips session state', () => {
    const raw = serializeFeedScrollSecretSession({ bottomHits: 2, triggered: false })
    expect(parseFeedScrollSecretSession(raw)).toEqual({ bottomHits: 2, triggered: false })
  })

  it('returns defaults for invalid json', () => {
    expect(parseFeedScrollSecretSession('not-json')).toEqual({ bottomHits: 0, triggered: false })
  })
})
