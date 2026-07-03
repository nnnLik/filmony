import { describe, expect, it } from 'vitest'

import {
  DEFAULT_RATED_CARDS_QUERY,
  mergeRatedCardsFilterSearchParams,
  ratedCardsQueryFromSearchParams,
  ratedCardsQueryKey,
  ratedCardsQueryToSearchParams,
} from '../ratedCardsListQuery'

describe('ratedCardsListQuery url helpers', () => {
  it('serializes only non-default filter values', () => {
    const query = {
      ...DEFAULT_RATED_CARDS_QUERY,
      sort: 'rating_desc' as const,
      filmTitle: 'thriller',
      tags: ['noir', 'neo-noir'],
      favoritesOnly: true,
    }

    const params = ratedCardsQueryToSearchParams(query)

    expect(params.get('sort')).toBe('rating_desc')
    expect(params.get('filmTitle')).toBe('thriller')
    expect(params.get('tags')).toBe('noir,neo-noir')
    expect(params.get('favoritesOnly')).toBe('1')
    expect(params.get('yearMin')).toBeNull()
  })

  it('restores a non-default filter query from search params', () => {
    const params = new URLSearchParams(
      'sort=rating_desc&filmTitle=thriller&tags=noir,neo-noir&favoritesOnly=1&company=friends&moodBefore=thrill&categoryId=3',
    )

    const query = ratedCardsQueryFromSearchParams(params)

    expect(query).toEqual({
      ...DEFAULT_RATED_CARDS_QUERY,
      sort: 'rating_desc',
      filmTitle: 'thriller',
      tags: ['noir', 'neo-noir'],
      favoritesOnly: true,
      company: 'friends',
      moodBefore: 'thrill',
      categoryId: '3',
    })
  })

  it('falls back to defaults for invalid search params', () => {
    const params = new URLSearchParams(
      'sort=invalid&company=unknown&moodBefore=bad&moodAfter=bad&favoritesOnly=maybe',
    )

    expect(ratedCardsQueryFromSearchParams(params)).toEqual(DEFAULT_RATED_CARDS_QUERY)
  })

  it('round-trips through url helpers', () => {
    const query = {
      ...DEFAULT_RATED_CARDS_QUERY,
      sort: 'rating_asc' as const,
      filmTitle: 'matrix',
      yearMin: '1990',
      yearMax: '2000',
      moodAfter: 'enjoyed' as const,
      categoryId: '12',
    }

    const restored = ratedCardsQueryFromSearchParams(ratedCardsQueryToSearchParams(query))

    expect(ratedCardsQueryKey(restored)).toBe(ratedCardsQueryKey(query))
  })

  it('replaces only filter keys when merging search params', () => {
    const existing = new URLSearchParams('filmTitle=old&tab=posts&sort=recent')
    const filters = ratedCardsQueryToSearchParams({
      ...DEFAULT_RATED_CARDS_QUERY,
      filmTitle: 'new',
      sort: 'rating_desc',
    })

    const merged = mergeRatedCardsFilterSearchParams(existing, filters)

    expect(merged.get('tab')).toBe('posts')
    expect(merged.get('filmTitle')).toBe('new')
    expect(merged.get('sort')).toBe('rating_desc')
  })
})
