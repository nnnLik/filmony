import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { runAuthBootstrap } from './authBootstrap'
import type { AuthStatus } from './auth-context'

const writeAuthSessionFlag = vi.fn()
const writeAccessToken = vi.fn()
const readAccessToken = vi.fn()
const apiFetch = vi.fn()
const apiFetchCredentialsOnly = vi.fn()
const authTelegram = vi.fn()

vi.mock('../api/client', () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
  apiFetchCredentialsOnly: (...args: unknown[]) => apiFetchCredentialsOnly(...args),
}))

vi.mock('../api/profileApi', () => ({
  authTelegram: (...args: unknown[]) => authTelegram(...args),
}))

vi.mock('../lib/filmonySession', () => ({
  readAccessToken: () => readAccessToken(),
  writeAccessToken: (...args: unknown[]) => writeAccessToken(...args),
  writeAuthSessionFlag: (...args: unknown[]) => writeAuthSessionFlag(...args),
}))

vi.mock('../lib/myProfileBundleCache', () => ({
  clearMyProfileBundleCache: vi.fn(),
}))

vi.mock('../lib/movieCardTagStatsStorage', () => ({
  clearMovieCardTagStatsSessionCaches: vi.fn(),
}))

vi.mock('../lib/userCardCategoriesStorage', () => ({
  clearUserCardCategoriesSessionCaches: vi.fn(),
}))

function mockResponse(ok: boolean, status = ok ? 200 : 401): Response {
  return {
    ok,
    status,
    text: async () => '',
    json: async () => ({}),
  } as Response
}

describe('runAuthBootstrap', () => {
  let states: AuthStatus[]

  beforeEach(() => {
    states = []
    readAccessToken.mockReturnValue(null)
    apiFetch.mockReset()
    apiFetchCredentialsOnly.mockReset()
    authTelegram.mockReset()
    writeAuthSessionFlag.mockReset()
    writeAccessToken.mockReset()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('resumes with stored bearer when probe succeeds', async () => {
    readAccessToken.mockReturnValue('valid-token')
    apiFetch.mockResolvedValueOnce(mockResponse(true))
    apiFetchCredentialsOnly.mockResolvedValue(mockResponse(false, 401))

    await runAuthBootstrap({
      runId: 1,
      isCurrent: () => true,
      setState: (status) => {
        states.push(status)
      },
      waitForInitDataRaw: async () => 'init-data',
    })

    expect(states).toEqual([{ kind: 'ready' }])
    expect(writeAuthSessionFlag).toHaveBeenCalledWith(true)
    expect(authTelegram).not.toHaveBeenCalled()
  })

  it('resumes from cookie when bearer is stale but HttpOnly session is valid', async () => {
    readAccessToken.mockReturnValue('stale-token')
    apiFetch.mockResolvedValueOnce(mockResponse(false, 401))
    apiFetchCredentialsOnly.mockResolvedValueOnce(mockResponse(true))

    await runAuthBootstrap({
      runId: 1,
      isCurrent: () => true,
      setState: (status) => {
        states.push(status)
      },
      waitForInitDataRaw: async () => '',
    })

    expect(states).toEqual([{ kind: 'ready' }])
    expect(writeAccessToken).toHaveBeenCalledWith(null)
    expect(authTelegram).not.toHaveBeenCalled()
  })

  it('falls back to authTelegram when resume probes fail', async () => {
    readAccessToken.mockReturnValue(null)
    apiFetchCredentialsOnly.mockResolvedValue(mockResponse(false, 401))
    authTelegram.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: 'fresh-token' }),
    })

    await runAuthBootstrap({
      runId: 1,
      isCurrent: () => true,
      setState: (status) => {
        states.push(status)
      },
      waitForInitDataRaw: async () => 'telegram-init',
    })

    expect(authTelegram).toHaveBeenCalledWith('telegram-init')
    expect(states).toEqual([{ kind: 'ready' }])
    expect(writeAccessToken).toHaveBeenCalledWith('fresh-token')
  })
})
