import { describe, expect, it } from 'vitest'

import {
  collectionKindForCatalogSource,
  collectionsCatalogEmptyMessage,
  collectionsCatalogSourceLabel,
  collectionsCatalogSubtitle,
} from '../collectionsCatalogSource'

describe('collectionsCatalogSource', () => {
  it('maps letterboxd tab to evergreen kind', () => {
    expect(collectionKindForCatalogSource('letterboxd')).toBe('evergreen')
  })

  it('maps oscars tab to seasonal kind', () => {
    expect(collectionKindForCatalogSource('oscars')).toBe('seasonal')
  })

  it('provides human labels', () => {
    expect(collectionsCatalogSourceLabel('letterboxd')).toBe('Letterboxd')
    expect(collectionsCatalogSourceLabel('oscars')).toBe('Оскары')
  })

  it('provides tab-specific copy', () => {
    expect(collectionsCatalogEmptyMessage('letterboxd')).toContain('Letterboxd')
    expect(collectionsCatalogEmptyMessage('oscars')).toContain('Оскар')
    expect(collectionsCatalogSubtitle('letterboxd')).toContain('Letterboxd')
    expect(collectionsCatalogSubtitle('oscars')).toContain('Оскар')
    expect(collectionsCatalogSubtitle('letterboxd')).toContain('закрывай')
  })
})
