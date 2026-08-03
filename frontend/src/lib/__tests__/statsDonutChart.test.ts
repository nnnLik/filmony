import { describe, expect, it } from 'vitest'

import {
  aggregateYearDistributionToDecades,
  buildConicGradient,
  findPeakRatedYear,
} from '../statsDonutChart'

describe('buildConicGradient', () => {
  it('returns transparent gradient when total is zero', () => {
    expect(buildConicGradient([{ count: 0, color: '#fff' }])).toBe('conic-gradient(transparent 0% 100%)')
  })

  it('builds proportional stops for non-zero segments', () => {
    const gradient = buildConicGradient([
      { count: 25, color: '#111' },
      { count: 75, color: '#222' },
    ])
    expect(gradient).toBe('conic-gradient(#111 0% 25%, #222 25% 100%)')
  })

  it('skips zero-count segments', () => {
    const gradient = buildConicGradient([
      { count: 10, color: '#aaa' },
      { count: 0, color: '#bbb' },
      { count: 30, color: '#ccc' },
    ])
    expect(gradient).toBe('conic-gradient(#aaa 0% 25%, #ccc 25% 100%)')
  })
})

describe('aggregateYearDistributionToDecades', () => {
  it('groups years into decade buckets sorted chronologically', () => {
    const buckets = aggregateYearDistributionToDecades([
      { year: 1998, count: 2 },
      { year: 2001, count: 5 },
      { year: 2008, count: 1 },
      { year: 1995, count: 3 },
    ])

    expect(buckets).toEqual([
      { label: '1990-е', decadeStart: 1990, decadeEnd: 1999, count: 5, value: '1990' },
      { label: '2000-е', decadeStart: 2000, decadeEnd: 2009, count: 6, value: '2000' },
    ])
  })
})

describe('findPeakRatedYear', () => {
  it('returns year with highest rated count', () => {
    expect(
      findPeakRatedYear([
        { year: 2010, count: 7 },
        { year: 2012, count: 12 },
      ]),
    ).toEqual({ year: 2012, count: 12 })
  })

  it('returns null when rated list is empty', () => {
    expect(findPeakRatedYear([])).toBeNull()
    expect(findPeakRatedYear(undefined)).toBeNull()
  })

  it('returns null when no positive counts exist', () => {
    expect(findPeakRatedYear([{ year: 2020, count: 0 }])).toBeNull()
  })
})
