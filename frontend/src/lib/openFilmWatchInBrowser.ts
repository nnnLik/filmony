import { isTMA } from '@telegram-apps/sdk'

import { createWatchParty } from '../api/watchPartyApi'
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

function confirmThen(onOk: () => void | Promise<void>): Promise<void> {
  return new Promise((resolve) => {
    const runOk = () => {
      void Promise.resolve(onOk()).then(() => {
        resolve()
      })
    }
    const wa = window.Telegram?.WebApp
    if (wa?.showConfirm) {
      wa.showConfirm(WATCH_IN_BROWSER_CONFIRM_MESSAGE, (ok) => {
        if (ok) {
          runOk()
        } else {
          resolve()
        }
      })
      return
    }
    if (window.confirm(WATCH_IN_BROWSER_CONFIRM_MESSAGE)) {
      runOk()
      return
    }
    resolve()
  })
}

export async function openFilmWatchInBrowserAfterParty(
  filmId: number | string,
  partySlug?: string | null,
): Promise<void> {
  if (typeof partySlug === 'string' && partySlug !== '') {
    openExternalUrl(filmWatchAbsoluteUrl(filmId, partySlug))
    return
  }
  try {
    const created = await createWatchParty(Number(filmId))
    openExternalUrl(filmWatchAbsoluteUrl(filmId, created.invite_slug))
  } catch {
    openExternalUrl(filmWatchAbsoluteUrl(filmId))
  }
}

export async function confirmAndOpenFilmWatchInBrowser(
  filmId: number | string,
  partySlug?: string | null,
): Promise<void> {
  await confirmThen(() => openFilmWatchInBrowserAfterParty(filmId, partySlug))
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
  void confirmAndOpenFilmWatchInBrowser(filmId, partySlug)
}
