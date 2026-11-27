import { describe, expect, it } from 'vitest'

import { filmRateCardPath } from '../watchLeaveRatePrompt'

describe('watchLeaveRatePrompt', () => {
  describe('filmRateCardPath', () => {
    it('returns edit path when rated myCardId is set and planned is absent', () => {
      expect(filmRateCardPath(42, { myCardId: 17 })).toBe('/cards/17/edit')
    })

    it('returns create-from-planned path when myCardId equals plannedCardId', () => {
      expect(filmRateCardPath(42, { myCardId: 17, plannedCardId: 17 })).toBe(
        '/cards/new?fromCard=17&intent=rate',
      )
    })

    it('returns create-from-planned path when only plannedCardId is set', () => {
      expect(filmRateCardPath(42, { plannedCardId: 9 })).toBe(
        '/cards/new?fromCard=9&intent=rate',
      )
    })

    it('returns new card path when myCardId is null, zero, or undefined and planned is absent', () => {
      expect(filmRateCardPath(42, { myCardId: null })).toBe('/cards/new?filmId=42')
      expect(filmRateCardPath(42, { myCardId: 0 })).toBe('/cards/new?filmId=42')
      expect(filmRateCardPath(42, { myCardId: undefined })).toBe('/cards/new?filmId=42')
      expect(filmRateCardPath(42)).toBe('/cards/new?filmId=42')
    })

    it('treats myCardId 0 as none when planned is also absent', () => {
      expect(filmRateCardPath(42, { myCardId: 0, plannedCardId: 0 })).toBe(
        '/cards/new?filmId=42',
      )
    })
  })
})
