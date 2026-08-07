import type { CollectionKind } from '../api/collectionsTypes'

export type CollectionsCatalogSource = 'letterboxd' | 'oscars'

export const COLLECTIONS_CATALOG_SOURCES: CollectionsCatalogSource[] = ['letterboxd', 'oscars']

export function collectionsCatalogSourceLabel(source: CollectionsCatalogSource): string {
  return source === 'letterboxd' ? 'Letterboxd' : 'Оскары'
}

export function collectionKindForCatalogSource(
  source: CollectionsCatalogSource,
): CollectionKind {
  return source === 'letterboxd' ? 'evergreen' : 'seasonal'
}

export function collectionsCatalogEmptyMessage(source: CollectionsCatalogSource): string {
  return source === 'letterboxd'
    ? 'Пока нет коллекций Letterboxd.'
    : 'Пока нет сезонных коллекций «Оскар».'
}

export function collectionsCatalogSubtitle(source: CollectionsCatalogSource): string {
  return source === 'letterboxd'
    ? 'Списки с Letterboxd — оценивай и закрывай.'
    : '«Оскар» за лучший фильм по годам — оценивай и закрывай.'
}
