/** Opens an https URL in the Telegram client when embedded, otherwise in a new tab. */
export function openExternalUrl(url: string): void {
  const wa = window.Telegram?.WebApp
  if (wa?.openLink) {
    wa.openLink(url)
    return
  }
  window.open(url, '_blank', 'noopener,noreferrer')
}

export function kinopoiskTitleUrl(kinopoiskId: number): string {
  return `https://www.kinopoisk.ru/film/${kinopoiskId}/`
}

import type { UserCardProvider } from '../api/profileTypes'

/** Numeric KP id: legacy `film_kinopoisk_id` or `external_id` string (digits only). */
export function kinopoiskNumericIdFromCard(
  filmKinopoiskId: number | null | undefined,
  provider: UserCardProvider,
  externalId: string | null | undefined,
): number | null {
  if (typeof filmKinopoiskId === 'number' && filmKinopoiskId > 0) {
    return filmKinopoiskId
  }
  if (provider !== 'kinopoisk') return null
  if (externalId == null) return null
  const raw = externalId.trim()
  if (raw === '') return null
  const n = Number(raw)
  return Number.isInteger(n) && n > 0 ? n : null
}

export function kinopoiskTitleUrlFromCard(
  filmKinopoiskId: number | null | undefined,
  provider: UserCardProvider,
  externalId: string | null | undefined,
): string | null {
  const id = kinopoiskNumericIdFromCard(filmKinopoiskId, provider, externalId)
  return id == null ? null : kinopoiskTitleUrl(id)
}
