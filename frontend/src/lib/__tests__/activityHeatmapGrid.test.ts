import { describe, expect, it } from 'vitest'

import {
  buildActivityHeatmapGrid,
  clipHeatmapWindow,
  countToHeatLevel,
  sumActivityCounts,
} from '../activityHeatmapGrid'

describe('activityHeatmapGrid', () => {
  it('clips heatmap window to last 30 days when range is longer', () => {
    expect(clipHeatmapWindow('2026-01-01', '2026-08-15')).toEqual({
      start: '2026-07-17',
      end: '2026-08-15',
    })
  })

  it('keeps activity start when API range is already shorter than 30 days', () => {
    expect(clipHeatmapWindow('2026-08-10', '2026-08-15')).toEqual({
      start: '2026-08-10',
      end: '2026-08-15',
    })
  })

  it('maps counts to heat levels', () => {
    expect(countToHeatLevel(0, 10)).toBe(0)
    expect(countToHeatLevel(1, 1)).toBe(1)
    expect(countToHeatLevel(2, 8)).toBe(2)
    expect(countToHeatLevel(4, 8)).toBe(3)
    expect(countToHeatLevel(6, 8)).toBe(4)
    expect(countToHeatLevel(8, 8)).toBe(4)
  })

  it('spreads 1, 5, and 50 films across different log1p heat levels', () => {
    expect(countToHeatLevel(0, 50)).toBe(0)
    const levelOne = countToHeatLevel(1, 50)
    const levelFive = countToHeatLevel(5, 50)
    const levelFifty = countToHeatLevel(50, 50)
    expect(levelOne).toBeGreaterThan(0)
    expect(levelFive).toBeGreaterThan(0)
    expect(levelFifty).toBeGreaterThan(0)
    expect(new Set([levelOne, levelFive, levelFifty]).size).toBe(3)
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
