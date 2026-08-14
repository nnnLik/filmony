import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  confirmAndOpenFilmWatchInBrowser,
  filmWatchAbsoluteUrl,
  filmWatchPath,
  onWatchCtaClick,
  WATCH_IN_BROWSER_CONFIRM_MESSAGE,
} from '../openFilmWatchInBrowser'

const mocks = vi.hoisted(() => ({
  isTMA: vi.fn<() => boolean>(),
  openExternalUrl: vi.fn<(url: string) => void>(),
}))

vi.mock('@telegram-apps/sdk', () => ({
  isTMA: mocks.isTMA,
}))

vi.mock('../openExternalUrl', () => ({
  openExternalUrl: mocks.openExternalUrl,
}))

const originalTelegram = window.Telegram
const originalConfirm = window.confirm

describe('openFilmWatchInBrowser', () => {
  beforeEach(() => {
    mocks.isTMA.mockReturnValue(false)
    mocks.openExternalUrl.mockReset()
  })

  afterEach(() => {
    window.Telegram = originalTelegram
    window.confirm = originalConfirm
    vi.clearAllMocks()
  })

  it('encodes film id in the watch path', () => {
    expect(filmWatchPath(42)).toBe('/films/42/watch')
    expect(filmWatchPath('foo/bar')).toBe('/films/foo%2Fbar/watch')
    expect(filmWatchPath('a b')).toBe('/films/a%20b/watch')
  })

  it('appends party query when slug is present and omits it when empty', () => {
    expect(filmWatchPath(1, 'abc')).toBe('/films/1/watch?party=abc')
    expect(filmWatchPath(1, 'a b')).toBe('/films/1/watch?party=a%20b')
    expect(filmWatchPath(1, '')).toBe('/films/1/watch')
    expect(filmWatchPath(1, null)).toBe('/films/1/watch')
    expect(filmWatchPath(1)).toBe('/films/1/watch')
    expect(filmWatchAbsoluteUrl(7, 'slug', 'https://example.com')).toBe(
      'https://example.com/films/7/watch?party=slug',
    )
    expect(filmWatchAbsoluteUrl(7, '', 'https://example.com')).toBe(
      'https://example.com/films/7/watch',
    )
  })

  it('opens the watch url after TMA showConfirm OK', () => {
    window.Telegram = {
      WebApp: {
        showConfirm: (_message, callback) => {
          callback?.(true)
        },
      },
    } as typeof window.Telegram

    confirmAndOpenFilmWatchInBrowser(7, 'abc-slug')

    expect(mocks.openExternalUrl).toHaveBeenCalledWith(
      `${window.location.origin}/films/7/watch?party=abc-slug`,
    )
  })

  it('does not open when TMA showConfirm is cancelled', () => {
    window.Telegram = {
      WebApp: {
        showConfirm: (_message, callback) => {
          callback?.(false)
        },
      },
    } as typeof window.Telegram

    confirmAndOpenFilmWatchInBrowser(7)

    expect(mocks.openExternalUrl).not.toHaveBeenCalled()
  })

  it('falls back to window.confirm when showConfirm is missing', () => {
    window.Telegram = undefined
    window.confirm = vi.fn(() => true)

    confirmAndOpenFilmWatchInBrowser(3)

    expect(window.confirm).toHaveBeenCalledWith(WATCH_IN_BROWSER_CONFIRM_MESSAGE)
    expect(mocks.openExternalUrl).toHaveBeenCalledWith(
      `${window.location.origin}/films/3/watch`,
    )
  })

  it('does not preventDefault on watch CTA when not in TMA', () => {
    mocks.isTMA.mockReturnValue(false)
    const preventDefault = vi.fn()

    onWatchCtaClick({ preventDefault }, 9)

    expect(preventDefault).not.toHaveBeenCalled()
    expect(mocks.openExternalUrl).not.toHaveBeenCalled()
  })

  it('prevents default on watch CTA when in TMA', () => {
    mocks.isTMA.mockReturnValue(true)
    window.Telegram = {
      WebApp: {
        showConfirm: () => undefined,
      },
    } as unknown as typeof window.Telegram
    const preventDefault = vi.fn()

    onWatchCtaClick({ preventDefault }, 9)

    expect(preventDefault).toHaveBeenCalled()
  })
})
