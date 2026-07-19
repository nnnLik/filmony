import { getFilmById } from '../api/cardApi'
import type { CreateWatchlistEntryBody, WatchTag } from '../api/profileApi'
import type { CardCompany, Film, MovieCard } from '../api/profileTypes'
import {
  creationBindingFromMovieCard,
  watchlistCustomCardId,
  type CreationBinding,
} from './createCardBinding'

export type WatchlistBinding =
  | CreationBinding
  | { kind: 'catalog_item'; catalogItemId: number }
  | {
      kind: 'manual_card'
      card_id: string
      display_title: string
      display_cover_url: string | null
      display_summary: string | null
    }

export function buildWatchlistCreatePayload(
  binding: WatchlistBinding,
  opts?: {
    watch_tag?: WatchTag
    company?: CardCompany
    category_id?: number | null
    watch_note?: string
    watch_with_user_ids?: string[]
  },
): CreateWatchlistEntryBody | null {
  const watchExtras: Omit<
    CreateWatchlistEntryBody,
    'film_id' | 'catalog_item_id' | 'card_id' | 'provider_meta'
  > = {
    watch_tag: opts?.watch_tag ?? 'watch_later',
    company: opts?.company ?? 'alone',
    watch_note: opts?.watch_note ?? '',
  }
  if (opts?.category_id != null && opts.category_id > 0) {
    watchExtras.category_id = opts.category_id
  }
  if (opts?.watch_with_user_ids != null && opts.watch_with_user_ids.length > 0) {
    watchExtras.watch_with_user_ids = opts.watch_with_user_ids
  }
  if (binding.kind === 'manual') {
    const title = binding.display_title.trim()
    if (title === '') return null
    return {
      card_id: watchlistCustomCardId(title),
      provider_meta: {
        provider: 'custom',
        data: {
          title,
          display_cover_url: binding.display_cover_url,
          display_summary: binding.display_summary,
        },
      },
      ...watchExtras,
    }
  }
  if (binding.kind === 'manual_card') {
    const title = binding.display_title.trim()
    if (title === '') return null
    return {
      card_id: binding.card_id,
      provider_meta: {
        provider: 'custom',
        data: {
          title,
          display_cover_url: binding.display_cover_url,
          display_summary: binding.display_summary,
        },
      },
      ...watchExtras,
    }
  }
  if (binding.kind === 'catalog_game' || binding.kind === 'catalog_item') {
    return { catalog_item_id: binding.catalogItemId, ...watchExtras }
  }
  if (binding.kind === 'catalog_film' || binding.kind === 'film') {
    return { film_id: binding.film.id, ...watchExtras }
  }
  return null
}

export async function watchlistBindingFromMovieCard(card: MovieCard): Promise<WatchlistBinding | null> {
  return creationBindingFromMovieCard(card)
}

export function watchlistBindingPreview(binding: WatchlistBinding): {
  posterUrl: string | null
  title: string
  yearLabel: string
  genres: string[]
} {
  if (binding.kind === 'manual' || binding.kind === 'manual_card') {
    return {
      posterUrl: binding.display_cover_url,
      title: binding.display_title,
      yearLabel: '—',
      genres: [],
    }
  }
  if (binding.kind === 'catalog_game') {
    const sub = (binding.subtitle ?? '').trim()
    return {
      posterUrl: binding.display_cover_url,
      title: binding.display_title,
      yearLabel: sub !== '' ? sub : 'Каталог RAWG',
      genres: [],
    }
  }
  if (binding.kind === 'catalog_item') {
    return {
      posterUrl: null,
      title: `Каталог #${binding.catalogItemId}`,
      yearLabel: '—',
      genres: [],
    }
  }
  const f = binding.film
  return {
    posterUrl: f.poster_url ?? null,
    title: f.title,
    yearLabel: f.year != null ? String(f.year) : 'Год неизвестен',
    genres: f.genres ?? [],
  }
}

export async function watchlistBindingFromFilmId(filmId: number): Promise<WatchlistBinding> {
  const item = await getFilmById(filmId)
  return { kind: 'film', film: item }
}

export function watchlistBindingFromCatalogItemId(catalogItemId: number): WatchlistBinding {
  return { kind: 'catalog_item', catalogItemId }
}

export function watchlistBindingFromCardId(cardId: string): WatchlistBinding {
  const title = cardId.startsWith('custom:')
    ? cardId.slice('custom:'.length).replace(/-/g, ' ')
    : cardId
  return {
    kind: 'manual_card',
    card_id: cardId,
    display_title: title,
    display_cover_url: null,
    display_summary: null,
  }
}

export type { Film }
