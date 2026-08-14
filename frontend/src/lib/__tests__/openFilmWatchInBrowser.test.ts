import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  confirmAndOpenFilmWatchInBrowser,
  filmWatchAbsoluteUrl,
  filmWatchPath,
  onWatchCtaClick,
  openFilmWatchInBrowserAfterParty,
  WATCH_IN_BROWSER_CONFIRM_MESSAGE,
} from '../openFilmWatchInBrowser'

const mocks = vi.hoisted(() => ({
  isTMA: vi.fn<() => boolean>(),
  openExternalUrl: vi.fn<(url: string) => void>(),
  createWatchParty: vi.fn<
    (filmId: number) => Promise<{ id: string; invite_slug: string; invite_url: string }>
  >(),
}))

vi.mock('@telegram-apps/sdk', () => ({
  isTMA: mocks.isTMA,
}))

vi.mock('../openExternalUrl', () => ({
  openExternalUrl: mocks.openExternalUrl,
}))

vi.mock('../../api/watchPartyApi', () => ({
  createWatchParty: mocks.createWatchParty,
}))

const originalTelegram = window.Telegram
const originalConfirm = window.confirm

describe('openFilmWatchInBrowser', () => {
  beforeEach(() => {
    mocks.isTMA.mockReturnValue(false)
    mocks.openExternalUrl.mockReset()
    mocks.createWatchParty.mockReset()
    mocks.createWatchParty.mockResolvedValue({
      id: 'party-1',
      invite_slug: 'new-party-slug',
      invite_url: 'https://example.com/party/new-party-slug',
    })
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

  it('opens watch url with existing party slug without creating a party', async () => {
    await openFilmWatchInBrowserAfterParty(7, 'existing-slug')

    expect(mocks.createWatchParty).not.toHaveBeenCalled()
    expect(mocks.openExternalUrl).toHaveBeenCalledWith(
      `${window.location.origin}/films/7/watch?party=existing-slug`,
    )
  })

  it('creates watch party and opens url with party slug after TMA showConfirm OK', async () => {
    window.Telegram = {
      WebApp: {
        showConfirm: (_message, callback) => {
          callback?.(true)
        },
      },
    } as typeof window.Telegram

    await confirmAndOpenFilmWatchInBrowser(7)

    expect(mocks.createWatchParty).toHaveBeenCalledWith(7)
    expect(mocks.openExternalUrl).toHaveBeenCalledWith(
      `${window.location.origin}/films/7/watch?party=new-party-slug`,
    )
  })

  it('opens watch url without party slug when createWatchParty fails', async () => {
    window.Telegram = {
      WebApp: {
        showConfirm: (_message, callback) => {
          callback?.(true)
        },
      },
    } as typeof window.Telegram
    mocks.createWatchParty.mockRejectedValue(new Error('network'))

    await confirmAndOpenFilmWatchInBrowser(7)

    expect(mocks.createWatchParty).toHaveBeenCalledWith(7)
    expect(mocks.openExternalUrl).toHaveBeenCalledWith(
      `${window.location.origin}/films/7/watch`,
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

    void confirmAndOpenFilmWatchInBrowser(7)

    expect(mocks.openExternalUrl).not.toHaveBeenCalled()
  })

  it('falls back to window.confirm when showConfirm is missing', async () => {
    window.Telegram = undefined
    window.confirm = vi.fn(() => true)

    await confirmAndOpenFilmWatchInBrowser(3)

    expect(window.confirm).toHaveBeenCalledWith(WATCH_IN_BROWSER_CONFIRM_MESSAGE)
    expect(mocks.createWatchParty).toHaveBeenCalledWith(3)
    expect(mocks.openExternalUrl).toHaveBeenCalledWith(
      `${window.location.origin}/films/3/watch?party=new-party-slug`,
    )
  })

  it('does not preventDefault on watch CTA when not in TMA', () => {
    mocks.isTMA.mockReturnValue(false)
    const preventDefault = vi.fn()

    void onWatchCtaClick({ preventDefault }, 9)

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

    void onWatchCtaClick({ preventDefault }, 9)

    expect(preventDefault).toHaveBeenCalled()
  })
})
