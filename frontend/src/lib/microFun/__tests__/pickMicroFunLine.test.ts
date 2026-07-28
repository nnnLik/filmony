import { describe, expect, it } from 'vitest'

import { MICRO_FUN_POOLS } from '../microFunCopy'
import {
  buildMicroFunSeedParts,
  pickMicroFunLine,
  pickMicroFunLineIndex,
} from '../pickMicroFunLine'

describe('pickMicroFunLine', () => {
  it('returns stable line for same seed parts', () => {
    const pool = MICRO_FUN_POOLS.comments_empty
    const seed = buildMicroFunSeedParts('comments_empty', 42, '2026-07-29')
    const a = pickMicroFunLine({ pool, seedParts: seed })
    const b = pickMicroFunLine({ pool, seedParts: seed })
    expect(a).toBe(b)
    expect(a).toBeTruthy()
  })

  it('may differ across pool keys for same user/day', () => {
    const userId = 7
    const day = '2026-07-29'
    const commentsIdx = pickMicroFunLineIndex(
      MICRO_FUN_POOLS.comments_empty.length,
      buildMicroFunSeedParts('comments_empty', userId, day),
    )
    const feedIdx = pickMicroFunLineIndex(
      MICRO_FUN_POOLS.feed_empty.length,
      buildMicroFunSeedParts('feed_empty', userId, day),
    )
    expect(typeof commentsIdx).toBe('number')
    expect(typeof feedIdx).toBe('number')
  })

  it('returns null for empty pool', () => {
    expect(pickMicroFunLine({ pool: [], seedParts: ['a'] })).toBeNull()
  })
})

describe('resolveMicroFunLine integration', () => {
  it('uses fallback when userId is null', async () => {
    const { resolveMicroFunLine } = await import('../resolveMicroFunLine')
    expect(
      resolveMicroFunLine({
        poolKey: 'feed_empty',
        fallback: 'neutral',
        userId: null,
      }),
    ).toBe('neutral')
  })
})
