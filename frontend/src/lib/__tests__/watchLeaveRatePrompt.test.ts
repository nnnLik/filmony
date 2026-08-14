import { describe, expect, it } from 'vitest'

import { filmRateCardPath } from '../watchLeaveRatePrompt'

describe('watchLeaveRatePrompt', () => {
  describe('filmRateCardPath', () => {
    it('returns edit path when myCardId is positive', () => {
      expect(filmRateCardPath(42, 17)).toBe('/cards/17/edit')
    })

    it('returns new card path when myCardId is null or zero', () => {
      expect(filmRateCardPath(42, null)).toBe('/cards/new?filmId=42')
      expect(filmRateCardPath(42, 0)).toBe('/cards/new?filmId=42')
    })

    it('returns new card path when myCardId is undefined', () => {
      expect(filmRateCardPath(99, undefined)).toBe('/cards/new?filmId=99')
    })
  })
})
