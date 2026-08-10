import { describe, expect, it } from 'vitest'

import { resolveStartParamToPath } from '../miniAppCardDeepLink'

describe('resolveStartParamToPath', () => {
  it('returns null for empty or unknown start_param', () => {
    expect(resolveStartParamToPath('')).toBeNull()
    expect(resolveStartParamToPath('   ')).toBeNull()
    expect(resolveStartParamToPath('unknown')).toBeNull()
  })

  it('resolves card deeplinks', () => {
    expect(resolveStartParamToPath('c42')).toEqual({
      path: '/cards/42',
      state: { cardEntry: 'telegram_start_param' },
    })
    expect(resolveStartParamToPath('C7')).toEqual({
      path: '/cards/7',
      state: { cardEntry: 'telegram_start_param' },
    })
    expect(resolveStartParamToPath('c0')).toBeNull()
  })

  it('resolves feed post deeplinks', () => {
    expect(resolveStartParamToPath('p99')).toEqual({
      path: '/feed-posts/99',
      state: { fromFeed: true },
    })
    expect(resolveStartParamToPath('p0')).toBeNull()
  })

  it('resolves film deeplinks', () => {
    expect(resolveStartParamToPath('f301')).toEqual({ path: '/films/301' })
    expect(resolveStartParamToPath('fabc')).toBeNull()
  })

  it('resolves watchlist deeplinks', () => {
    const cardId = 'invite-card'
    const encoded = btoa(String.fromCharCode(...new TextEncoder().encode(cardId)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '')

    expect(resolveStartParamToPath(`w${encoded}`)).toEqual({
      path: '/profile?movies=watchlist',
      state: { watchlistInviteCardId: cardId },
    })
  })

  it('resolves taste quiz deeplinks', () => {
    expect(resolveStartParamToPath('tqabc-token_1')).toEqual({
      path: '/taste-quiz/invite/abc-token_1',
    })
  })

  it('resolves watch party deeplinks', () => {
    expect(resolveStartParamToPath('wpabc123token')).toEqual({
      path: '/watch-party/abc123token',
    })
    expect(resolveStartParamToPath('wp_abc123token')).toEqual({
      path: '/watch-party/abc123token',
    })
  })

  it('resolves recap deeplinks', () => {
    expect(resolveStartParamToPath('mr2024-3')).toEqual({
      path: '/me/recap/2024/3',
    })
    expect(resolveStartParamToPath('r202312')).toEqual({
      path: '/me/recap/2023/12',
    })
    expect(resolveStartParamToPath('mr2024-13')).toBeNull()
  })

  it('resolves weekly digest deeplinks', () => {
    expect(resolveStartParamToPath('wd2026-W19')).toEqual({
      path: '/me/digest/week/2026-W19',
    })
    expect(resolveStartParamToPath('wd2026-w19')).toEqual({
      path: '/me/digest/week/2026-W19',
    })
    expect(resolveStartParamToPath('wd2026-W99')).toBeNull()
  })
})
