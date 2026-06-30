import { beforeEach, describe, expect, it } from 'vitest'

import type { GlobalFeedKind } from '../../api/profileTypes'
import {
  FEED_SCROLL_STORAGE_KEY,
  readFeedScrollSnapshot,
  saveFeedScrollSnapshot,
} from '../feedScrollRestore'

describe('feedScrollRestore', () => {
  const kind = 'all' as GlobalFeedKind

  beforeEach(() => {
    localStorage.clear()
  })

  it('clears legacy storage on save', () => {
    localStorage.setItem(
      FEED_SCROLL_STORAGE_KEY,
      JSON.stringify({ kind: 'all', y: 120 }),
    )

    saveFeedScrollSnapshot(kind, 120)

    expect(localStorage.getItem(FEED_SCROLL_STORAGE_KEY)).toBeNull()
  })

  it('clears legacy storage on read and returns null', () => {
    localStorage.setItem(
      FEED_SCROLL_STORAGE_KEY,
      JSON.stringify({ kind: 'all', y: 120 }),
    )

    expect(readFeedScrollSnapshot()).toBeNull()
    expect(localStorage.getItem(FEED_SCROLL_STORAGE_KEY)).toBeNull()
  })
})
