import { getFilmById, resolveFilmByKinopoiskUrl } from '../api/cardApi'
import type { CatalogCandidate, CatalogResolveByUrlResponse } from '../api/catalogApi'
import type { GetMyPlannedCardParams } from '../api/profileApi'
import type { Film, MovieCard } from '../api/profileTypes'
import {
  movieCardPrimaryPoster,
  movieCardPrimaryTitle,
  movieCardReleaseCompactSuffix,
} from './movieCardDisplay'

export type CreationBinding =
  | { kind: 'film'; film: Film }
  | { kind: 'catalog_film'; catalogItemId: number; film: Film }
  | {
      kind: 'catalog_game'
      catalogItemId: number
      display_title: string
      display_cover_url: string | null
      display_summary: string | null
      subtitle: string | null
    }
  | {
      kind: 'manual'
      display_title: string
      display_cover_url: string | null
      display_summary: string | null
    }

export function watchlistCustomCardId(title: string): string {
  const slug =
    title
      .trim()
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s-]/gu, '')
      .replace(/\s+/g, '-')
      .slice(0, 80) || 'untitled'
  return `custom:${slug}`
}

export function plannedCardLookupParams(binding: CreationBinding): GetMyPlannedCardParams | null {
  if (binding.kind === 'film' || binding.kind === 'catalog_film') {
    return { film_id: binding.film.id }
  }
  if (binding.kind === 'catalog_game') {
    return { catalog_item_id: binding.catalogItemId }
  }
  if (binding.kind === 'manual') {
    const title = binding.display_title.trim()
    if (title === '') return null
    return { card_id: watchlistCustomCardId(title) }
  }
  return null
}

export async function creationBindingFromMovieCard(card: MovieCard): Promise<CreationBinding | null> {
  if (card.film_id != null && card.film_id > 0) {
    const item = await getFilmById(card.film_id)
    return { kind: 'film', film: item }
  }
  if (card.catalog_item_id != null && card.catalog_item_id > 0 && card.provider === 'rawg') {
    return {
      kind: 'catalog_game',
      catalogItemId: card.catalog_item_id,
      display_title: movieCardPrimaryTitle(card),
      display_cover_url: movieCardPrimaryPoster(card),
      display_summary: card.display_summary ?? null,
      subtitle: movieCardReleaseCompactSuffix(card),
    }
  }
  return {
    kind: 'manual',
    display_title: movieCardPrimaryTitle(card),
    display_cover_url: movieCardPrimaryPoster(card),
    display_summary: card.display_summary ?? null,
  }
}

export function bindingDisplayTitle(binding: CreationBinding): string {
  if (binding.kind === 'manual' || binding.kind === 'catalog_game') {
    return binding.display_title
  }
  return binding.film.title
}

export function bindingDisplayCover(binding: CreationBinding): string | null {
  if (binding.kind === 'manual' || binding.kind === 'catalog_game') {
    return binding.display_cover_url
  }
  return binding.film.poster_url ?? null
}

export function bindingDisplaySummary(binding: CreationBinding): string | null {
  if (binding.kind === 'manual') {
    return binding.display_summary
  }
  if (binding.kind === 'catalog_game') {
    return binding.display_summary
  }
  return binding.film.short_description ?? binding.film.description ?? null
}

export function bindingSubtitle(binding: CreationBinding): string | null {
  if (binding.kind === 'catalog_game') {
    const sub = (binding.subtitle ?? '').trim()
    return sub !== '' ? sub : 'Каталог RAWG'
  }
  if (binding.kind === 'manual') {
    return null
  }
  const f = binding.film
  return f.year != null ? String(f.year) : 'Год неизвестен'
}

export function kinopoiskCatalogRowHasMyCard(f: Film): boolean {
  return f.my_card_id != null && f.my_card_id > 0
}

export function bindingHasRatedDuplicate(binding: CreationBinding): { has: boolean; myCardId: number | null } {
  if (binding.kind === 'film' || binding.kind === 'catalog_film') {
    const id = binding.film.my_card_id
    if (id != null && id > 0) {
      return { has: true, myCardId: id }
    }
  }
  return { has: false, myCardId: null }
}

export function createManualBinding(
  title: string,
  coverUrl?: string | null,
  summary?: string | null,
): CreationBinding {
  const trimmedTitle = title.trim()
  const cover = (coverUrl ?? '').trim()
  const sum = (summary ?? '').trim()
  return {
    kind: 'manual',
    display_title: trimmedTitle,
    display_cover_url: cover === '' ? null : cover,
    display_summary: sum === '' ? null : sum,
  }
}

async function hydrateKinopoiskCatalogFilm(externalId: string): Promise<Film> {
  const id = externalId.trim()
  try {
    return await resolveFilmByKinopoiskUrl(`https://www.kinopoisk.ru/film/${id}/`)
  } catch (firstErr) {
    try {
      return await resolveFilmByKinopoiskUrl(`https://www.kinopoisk.ru/series/${id}/`)
    } catch {
      throw firstErr
    }
  }
}

export async function bindingFromCatalogCandidate(candidate: CatalogCandidate): Promise<CreationBinding> {
  if (candidate.catalog_item_id == null) {
    throw new Error('missing catalog_item_id')
  }
  if (candidate.kind === 'game') {
    const title = candidate.title.trim()
    if (title === '') {
      throw new Error('empty title')
    }
    return {
      kind: 'catalog_game',
      catalogItemId: candidate.catalog_item_id,
      display_title: title,
      display_cover_url: candidate.cover_url,
      display_summary: null,
      subtitle: candidate.subtitle,
    }
  }
  const film = await hydrateKinopoiskCatalogFilm(candidate.external_id)
  return {
    kind: 'catalog_film',
    catalogItemId: candidate.catalog_item_id,
    film,
  }
}

export function bindingFromResolveByUrl(resolved: CatalogResolveByUrlResponse): CreationBinding {
  return {
    kind: 'catalog_film',
    catalogItemId: resolved.catalog_item_id,
    film: resolved.film,
  }
}

/** После мастера создания сохраняем returnTo=feed в URL при strip query-параметров. */
export function cardsNewPathPreserveReturnTo(returnTo: string | null): string {
  return returnTo === 'feed' ? '/cards/new?returnTo=feed' : '/cards/new'
}

export function mapResolveError(detail: string): string {
  const normalized = detail.toLowerCase()
  if (normalized.includes('empty url')) {
    return 'Вставьте ссылку на страницу записи каталога на Кинопоиске.'
  }
  if (normalized.includes('url must be from kinopoisk.ru') || normalized.includes('unsupported host')) {
    return 'Нужна ссылка с домена kinopoisk.ru.'
  }
  if (
    normalized.includes('kinopoisk id was not found in url') ||
    normalized.includes('film id was not found in url')
  ) {
    return 'Не получилось прочитать номер из ссылки. Скопируйте полный адрес страницы на Кинопоиске (из строки браузера).'
  }
  return detail
}

export function normalizeRating(value: number): number {
  const clamped = Math.max(1, Math.min(10, value))
  return Math.round(clamped * 2) / 2
}

export function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

export const CREATE_CARD_TEXT_FIELD_CLASS =
  'w-full min-h-11 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-3 py-2.5 text-sm text-(--tgui--text_color) outline-none transition-[border-color,box-shadow] placeholder:text-(--tgui--hint_color) focus-visible:border-(--tgui--link_color) focus-visible:ring-2 focus-visible:ring-[color-mix(in_srgb,var(--tgui--link_color)_32%,transparent)]'

/** Совпадает с бэкендом `create_movie_card._normalize_tags`. */
export const MAX_CUSTOM_TAG_LEN = 40
