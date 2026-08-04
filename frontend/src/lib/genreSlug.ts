/** Stable URL slug for genre display names (mirrors backend `lib/genre_slug.py`). */
export function genreSlug(name: string): string {
  const normalized = name.trim().toLowerCase().normalize('NFKD')
  const asciiOnly = normalized.replace(/[\u0300-\u036f]/g, '').replace(/[\u0080-\uFFFF]/g, '')
  const slug = asciiOnly.replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
  return slug === '' ? 'unknown' : slug
}
