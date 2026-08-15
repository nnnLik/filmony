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

export function similarSummary(titles: string[]): string {
  if (titles.length === 0) return ''
  if (titles.length === 1) return titles[0] ?? ''
  return formatFilmsCount(titles.length)
}
