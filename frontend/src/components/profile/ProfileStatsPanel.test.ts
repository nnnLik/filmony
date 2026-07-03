import { describe, expect, it } from 'vitest'

import { mergeShelfDistributionWithMetadata } from '../../lib/profileShelfDistribution'

describe('mergeShelfDistributionWithMetadata', () => {
  it('adds zero-count shelves from metadata and preserves existing counts', () => {
    const merged = mergeShelfDistributionWithMetadata(
      [
        { category_id: 11, name: 'Action', count: 2 },
        { category_id: null, name: 'Без полки', count: 1 },
      ],
      [
        { id: 11, name: 'Action', created_at: '2026-07-03T00:00:00Z' },
        { id: 12, name: 'Drama', created_at: '2026-07-03T00:00:00Z' },
      ],
    )

    expect(merged).toEqual([
      { category_id: 11, name: 'Action', count: 2 },
      { category_id: 12, name: 'Drama', count: 0 },
      { category_id: null, name: 'Без полки', count: 1 },
    ])
  })

  it('falls back to stats rows when metadata is unavailable', () => {
    const merged = mergeShelfDistributionWithMetadata(
      [{ category_id: 99, name: 'Legacy shelf', count: 4 }],
      [],
    )

    expect(merged).toEqual([{ category_id: 99, name: 'Legacy shelf', count: 4 }])
  })
})
