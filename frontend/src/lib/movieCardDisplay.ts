import type { MovieCard, ProfileStatsMovieItem } from '../api/profileTypes'
import { kinopoiskNumericIdFromCard } from './openExternalUrl'
import type { FeedPostReferencedCard } from '../api/feedInFeedTypes'

/** Primary title: user-owned display field first, then legacy film title. */
export function movieCardPrimaryTitle(card: Pick<MovieCard, 'display_title' | 'film_title'>): string {
  const raw = card.display_title
  const d = typeof raw === 'string' ? raw.trim() : ''
  if (d !== '') return d
  return card.film_title
}

/** Primary poster URL: display cover first, then legacy film poster. */
export function movieCardPrimaryPoster(card: Pick<MovieCard, 'display_cover_url' | 'film_poster_url'>): string | null {
  const c = card.display_cover_url
  if (typeof c === 'string') {
    const t = c.trim()
    if (t !== '') return t
  }
  return card.film_poster_url ?? null
}

/** Synopsis / summary for detail: display summary first, then film text fields. */
export function movieCardPrimarySummary(
  card: Pick<MovieCard, 'display_summary' | 'film_short_description' | 'film_description'>,
): string | null {
  const ds = card.display_summary
  if (typeof ds === 'string') {
    const t = ds.trim()
    if (t !== '') return t
  }
  return card.film_short_description ?? card.film_description ?? null
}

export function movieCardHasKinopoiskLink(
  card: Pick<MovieCard, 'film_kinopoisk_id' | 'provider' | 'external_id'>,
): boolean {
  return kinopoiskNumericIdFromCard(card.film_kinopoisk_id, card.provider, card.external_id) != null
}

export function feedPostReferencedCardTitle(ref: FeedPostReferencedCard): string {
  const d = ref.display_title
  if (typeof d === 'string') {
    const t = d.trim()
    if (t !== '') return t
  }
  return ref.film_title
}

export function feedPostReferencedCardPoster(ref: FeedPostReferencedCard): string | null {
  const c = ref.display_cover_url
  if (typeof c === 'string') {
    const t = c.trim()
    if (t !== '') return t
  }
  return ref.film_poster_url ?? null
}

export function profileStatsMoviePrimaryTitle(
  row: Pick<ProfileStatsMovieItem, 'display_title' | 'film_title'>,
): string {
  const d = row.display_title
  if (typeof d === 'string') {
    const t = d.trim()
    if (t !== '') return t
  }
  return row.film_title
}

export function profileStatsMoviePrimaryPoster(
  row: Pick<ProfileStatsMovieItem, 'display_cover_url' | 'film_poster_url'>,
): string | null {
  const c = row.display_cover_url
  if (typeof c === 'string') {
    const t = c.trim()
    if (t !== '') return c
  }
  return row.film_poster_url ?? null
}
