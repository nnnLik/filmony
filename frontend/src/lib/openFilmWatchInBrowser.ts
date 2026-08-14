import { isTMA } from '@telegram-apps/sdk'

import { openExternalUrl } from './openExternalUrl'

export const WATCH_IN_BROWSER_CONFIRM_MESSAGE =
  'Вы будете перенаправлены в браузер для просмотра фильма.'

export function filmWatchPath(filmId: number | string, partySlug?: string | null): string {
  const path = `/films/${encodeURIComponent(String(filmId))}/watch`
  if (typeof partySlug === 'string' && partySlug !== '') {
    return `${path}?party=${encodeURIComponent(partySlug)}`
  }
  return path
}

export function filmWatchAbsoluteUrl(
  filmId: number | string,
  partySlug?: string | null,
  origin?: string,
): string {
  const base = origin ?? window.location.origin
  return `${base}${filmWatchPath(filmId, partySlug)}`
}

function confirmThen(onOk: () => void): void {
  const wa = window.Telegram?.WebApp
  if (wa?.showConfirm) {
    wa.showConfirm(WATCH_IN_BROWSER_CONFIRM_MESSAGE, (ok) => {
      if (ok) {
        onOk()
      }
    })
    return
  }
  if (window.confirm(WATCH_IN_BROWSER_CONFIRM_MESSAGE)) {
    onOk()
  }
}

export function confirmAndOpenFilmWatchInBrowser(
  filmId: number | string,
  partySlug?: string | null,
): void {
  confirmThen(() => {
    openExternalUrl(filmWatchAbsoluteUrl(filmId, partySlug))
  })
}

export function onWatchCtaClick(
  event: { preventDefault(): void },
  filmId: number | string,
  partySlug?: string | null,
): void {
  if (!isTMA()) {
    return
  }
  event.preventDefault()
  confirmAndOpenFilmWatchInBrowser(filmId, partySlug)
}
