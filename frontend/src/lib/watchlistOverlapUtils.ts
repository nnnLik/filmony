import type { MovieCard, WatchlistOverlapItem } from '../api/profileTypes'
import { watchlistCustomCardId, watchlistYoutubeCardId } from './createCardBinding'

export type WatchlistOverlapAnchor = {
  card_id?: string | null
  film_id?: number | null
  catalog_item_id?: number | null
}

export function findWatchlistOverlapForAnchor(
  items: WatchlistOverlapItem[],
  anchor: WatchlistOverlapAnchor,
): WatchlistOverlapItem | null {
  const cardId = anchor.card_id?.trim() ?? ''
  const filmId = anchor.film_id ?? null
  const catalogItemId = anchor.catalog_item_id ?? null

  for (const item of items) {
    if (cardId !== '' && item.card_id === cardId) {
      return item
    }
    if (filmId != null && filmId > 0 && item.film_id === filmId) {
      return item
    }
    if (catalogItemId != null && catalogItemId > 0 && item.catalog_item_id === catalogItemId) {
      return item
    }
  }
  return null
}

export function watchlistOverlapAnchorFromMovieCard(card: MovieCard): WatchlistOverlapAnchor {
  const anchor: WatchlistOverlapAnchor = {}
  if (card.film_id != null && card.film_id > 0) {
    anchor.film_id = card.film_id
  }
  if (card.catalog_item_id != null && card.catalog_item_id > 0) {
    anchor.catalog_item_id = card.catalog_item_id
  }
  if (card.provider === 'kinopoisk' && card.film_kinopoisk_id != null && card.film_kinopoisk_id > 0) {
    anchor.card_id = `kp:${card.film_kinopoisk_id}`
  } else if (card.provider === 'youtube' && card.external_id != null && card.external_id.trim() !== '') {
    anchor.card_id = watchlistYoutubeCardId(card.external_id.trim())
  } else if (card.provider === 'no_provider') {
    const title = card.display_title.trim()
    if (title !== '') {
      anchor.card_id = watchlistCustomCardId(title)
    }
  }
  return anchor
}

export function buildWatchlistNewHref(item: WatchlistOverlapItem): string {
  const params = new URLSearchParams()
  if (item.film_id != null && item.film_id > 0) {
    params.set('filmId', String(item.film_id))
  } else if (item.catalog_item_id != null && item.catalog_item_id > 0) {
    params.set('catalogItemId', String(item.catalog_item_id))
  } else if (item.card_id.trim() !== '') {
    params.set('watchlistCardId', item.card_id)
  }
  const partnerIds = item.partners.map((p) => p.user_id).filter((id) => id.trim() !== '')
  if (partnerIds.length > 0) {
    params.set('watchWithUserIds', partnerIds.join(','))
    params.set('company', 'friends')
  }
  return `/watchlist/new?${params.toString()}`
}

export function parseWatchWithUserIdsParam(raw: string | null): string[] {
  if (raw == null || raw.trim() === '') {
    return []
  }
  const seen = new Set<string>()
  const out: string[] = []
  for (const part of raw.split(',')) {
    const id = part.trim()
    if (id === '' || seen.has(id)) continue
    seen.add(id)
    out.push(id)
  }
  return out
}
