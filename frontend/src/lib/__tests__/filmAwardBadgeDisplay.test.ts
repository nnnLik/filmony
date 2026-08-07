import { describe, expect, it } from 'vitest'

import {
  oscarBadgeAriaLabel,
  oscarBadgeTitle,
  primaryFilmAwardBadge,
  releaseYearLabel,
} from '../filmAwardBadgeDisplay'

describe('filmAwardBadgeDisplay', () => {
  it('primaryFilmAwardBadge prefers winner then newest ceremony', () => {
    const badges = [
      { kind: 'oscar_best_picture_nominee' as const, ceremony_year: 2020 },
      { kind: 'oscar_best_picture_winner' as const, ceremony_year: 2024 },
      { kind: 'oscar_best_picture_nominee' as const, ceremony_year: 2023 },
    ]
    expect(primaryFilmAwardBadge(badges)?.ceremony_year).toBe(2024)
  })

  it('labels use release year and mention ceremony in tooltip copy', () => {
    const badge = { kind: 'oscar_best_picture_winner' as const, ceremony_year: 2024 }
    expect(oscarBadgeTitle(badge, 2023)).toContain('2023')
    expect(oscarBadgeTitle(badge, 2023)).toContain('церемония 2024')
    expect(oscarBadgeTitle(badge, 2023)).not.toMatch(/^.*2024.*лучший фильм.*2023/s)
    expect(oscarBadgeAriaLabel(badge, 2023)).toBe(oscarBadgeTitle(badge, 2023))
  })

  it('releaseYearLabel formats null as dash', () => {
    expect(releaseYearLabel(null)).toBe('—')
    expect(releaseYearLabel(2023)).toBe('2023')
  })
})
