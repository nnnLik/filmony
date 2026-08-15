import type { FilmRecommendationItem } from '../api/profileTypes'
import { formatFilmsCount } from './formatRuPlural'

export type FilmCatalogMetadataSize = 'sm' | 'md'
export type FilmCatalogMetadataVariant = 'compact' | 'full'

export const FILM_CATALOG_TEXT_SIZE: Record<FilmCatalogMetadataSize, string> = {
  sm: 'text-[11px] leading-snug sm:text-xs',
  md: 'text-xs leading-snug sm:text-sm',
}

export function normalizeMetadataStrings(values: string[] | null | undefined): string[] {
  return (values ?? []).map((value) => value.trim()).filter((value) => value !== '')
}

export function providersSummary(names: string[]): string {
  if (names.length === 0) return ''
  const preview = names.slice(0, 2).join(', ')
  const remainder = names.length - 2
  return remainder > 0 ? `${preview} +${remainder}` : preview
}

export function normalizeFilmRecommendations(
  items: FilmRecommendationItem[] | null | undefined,
): FilmRecommendationItem[] {
  return (items ?? [])
    .map((item) => ({
      title: item.title.trim(),
      film_id: item.film_id,
      in_catalog: item.in_catalog,
    }))
    .filter((item) => item.title !== '')
}

export function similarSummary(items: FilmRecommendationItem[]): string {
  if (items.length === 0) return ''
  if (items.length === 1) return items[0]?.title ?? ''
  return formatFilmsCount(items.length)
}
