export type CatalogCommunityKind = 'film' | 'game'

export function catalogCommunityPath(
  catalogItemId: number,
  kind: CatalogCommunityKind | null | undefined,
): string {
  if (kind === 'game') {
    return `/games/${encodeURIComponent(String(catalogItemId))}`
  }
  return `/catalog/${encodeURIComponent(String(catalogItemId))}`
}

export function filmCommunityPath(filmId: number): string {
  return `/films/${encodeURIComponent(String(filmId))}`
}
