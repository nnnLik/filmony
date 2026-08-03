import { describe, expect, it } from 'vitest'

import type { MarathonAchievement } from '../../api/gamificationTypes'
import { DEFAULT_RATED_CARDS_QUERY } from '../ratedCardsListQuery'
import { marathonDrillToRatedQuery } from '../marathonDrillToRatedQuery'

function marathon(partial: Partial<MarathonAchievement> & Pick<MarathonAchievement, 'kind' | 'key' | 'label'>): MarathonAchievement {
  return {
    count: 5,
    unlocked_at: '2026-01-01T00:00:00Z',
    sample_poster_urls: [],
    ...partial,
  }
}

describe('marathonDrillToRatedQuery', () => {
  it('sets director filter by kinopoisk id and clears title search', () => {
    const next = marathonDrillToRatedQuery(
      { ...DEFAULT_RATED_CARDS_QUERY, filmTitle: 'old' },
      marathon({ kind: 'director', key: '66539', label: 'Квентин Тарантино' }),
    )

    expect(next.directorKinopoiskId).toBe('66539')
    expect(next.franchiseKey).toBe('')
    expect(next.filmTitle).toBe('')
  })

  it('sets franchise filter and clears director/title', () => {
    const next = marathonDrillToRatedQuery(
      DEFAULT_RATED_CARDS_QUERY,
      marathon({ kind: 'franchise', key: 'kp_franchise:301', label: 'Франшиза 301' }),
    )

    expect(next.franchiseKey).toBe('kp_franchise:301')
    expect(next.directorKinopoiskId).toBe('')
    expect(next.filmTitle).toBe('')
  })
})
