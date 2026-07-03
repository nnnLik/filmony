import { describe, expect, it } from 'vitest'

import {
  buildActivityHeatmapGrid,
  countToHeatLevel,
  sumActivityCounts,
} from '../activityHeatmapGrid'

describe('activityHeatmapGrid', () => {
  it('maps counts to heat levels', () => {
    expect(countToHeatLevel(0, 10)).toBe(0)
    expect(countToHeatLevel(2, 8)).toBe(1)
    expect(countToHeatLevel(4, 8)).toBe(2)
    expect(countToHeatLevel(6, 8)).toBe(3)
    expect(countToHeatLevel(8, 8)).toBe(4)
  })

  it('builds a 7-row grid with week columns', () => {
    const grid = buildActivityHeatmapGrid(
      [
        { date: '2026-06-01', count: 2 },
        { date: '2026-06-02', count: 1 },
      ],
      '2026-06-01',
      '2026-06-07',
    )
    expect(grid).toHaveLength(7)
    expect(grid[0]?.length).toBeGreaterThan(0)
    expect(sumActivityCounts([{ date: '2026-06-01', count: 2 }])).toBe(2)
  })
})
