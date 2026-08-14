import { describe, expect, it } from 'vitest'

import {
  formatFilmAgeLimit,
  formatFilmDurationMinutes,
  formatFilmRating,
  formatFilmSlogan,
  hasFilmPassportData,
  joinFilmWatchProviders,
} from '../filmPassportDisplay'

describe('filmPassportDisplay', () => {
  it('formats duration, age limit, and ratings', () => {
    expect(formatFilmDurationMinutes(136)).toBe('2ч 16м')
    expect(formatFilmAgeLimit('age16')).toBe('16+')
    expect(formatFilmRating(8.47)).toBe('8.5')
  })

  it('detects when passport data is present', () => {
    expect(hasFilmPassportData({ film_length: 90 })).toBe(true)
    expect(hasFilmPassportData({})).toBe(false)
  })

  it('formats slogan and watch providers', () => {
    expect(formatFilmSlogan('  Welcome  ')).toBe('Welcome')
    expect(formatFilmSlogan('   ')).toBeNull()
    expect(joinFilmWatchProviders(['Okko', ' ', 'ivi'])).toBe('Okko · ivi')
    expect(joinFilmWatchProviders([])).toBeNull()
  })
})
