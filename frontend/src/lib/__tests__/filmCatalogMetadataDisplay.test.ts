import { describe, expect, it } from 'vitest'

import {
  normalizeMetadataStrings,
  providersSummary,
  similarSummary,
} from '../filmCatalogMetadataDisplay'

describe('filmCatalogMetadataDisplay', () => {
  it('normalizes metadata string lists', () => {
    expect(normalizeMetadataStrings([' Okko ', '', 'ivi'])).toEqual(['Okko', 'ivi'])
    expect(normalizeMetadataStrings(null)).toEqual([])
  })

  it('summarizes providers and similar titles', () => {
    expect(providersSummary(['Okko', 'ivi', 'Kinopoisk HD'])).toBe('Okko, ivi +1')
    expect(similarSummary(['Один'])).toBe('Один')
    expect(similarSummary(['A', 'B', 'C'])).toBe('3 фильма')
  })
})
