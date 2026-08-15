import { describe, expect, it } from 'vitest'

import {
  normalizeFilmRecommendations,
  normalizeMetadataStrings,
  providersSummary,
  similarSummary,
} from '../filmCatalogMetadataDisplay'

describe('filmCatalogMetadataDisplay', () => {
  it('normalizes metadata string lists', () => {
    expect(normalizeMetadataStrings([' Okko ', '', 'ivi'])).toEqual(['Okko', 'ivi'])
    expect(normalizeMetadataStrings(null)).toEqual([])
  })

  it('normalizes film recommendation items', () => {
    expect(
      normalizeFilmRecommendations([
        { title: ' Dark City ', in_catalog: true, film_id: 1 },
        { title: '', in_catalog: false },
        { title: 'Equilibrium', in_catalog: false },
      ]),
    ).toEqual([
      { title: 'Dark City', in_catalog: true, film_id: 1 },
      { title: 'Equilibrium', in_catalog: false, film_id: undefined },
    ])
    expect(normalizeFilmRecommendations(null)).toEqual([])
  })

  it('summarizes providers and similar titles', () => {
    expect(providersSummary(['Okko', 'ivi', 'Kinopoisk HD'])).toBe('Okko, ivi +1')
    expect(similarSummary([{ title: 'Один', in_catalog: true, film_id: 1 }])).toBe('Один')
    expect(
      similarSummary([
        { title: 'A', in_catalog: true, film_id: 1 },
        { title: 'B', in_catalog: false },
        { title: 'C', in_catalog: false },
      ]),
    ).toBe('3 фильма')
  })
})
