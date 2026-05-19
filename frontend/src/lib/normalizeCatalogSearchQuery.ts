/** Trim, collapse internal whitespace, lowercase — stable catalog search key and API `q`. */
export function normalizeCatalogSearchQuery(raw: string): string {
  return raw
    .trim()
    .split(/\s+/)
    .filter((p) => p.length > 0)
    .join(' ')
    .toLowerCase()
}
