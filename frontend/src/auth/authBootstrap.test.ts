import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { runAuthBootstrap } from './authBootstrap'
import type { AuthStatus } from './auth-context'

const mocks = vi.hoisted(() => ({
  writeAuthSessionFlag: vi.fn<(value: boolean) => void>(),
  writeAccessToken: vi.fn<(value: string | null) => void>(),
  readAccessToken: vi.fn<() => string | null>(),
  apiFetch: vi.fn<(path: string, init?: RequestInit) => Promise<Response>>(),
  apiFetchCredentialsOnly: vi.fn<(path: string, init?: RequestInit) => Promise<Response>>(),
  authTelegram: vi.fn<(raw: string) => Promise<Response>>(),
}))

vi.mock('../api/client', () => ({
  apiFetch: mocks.apiFetch,
  apiFetchCredentialsOnly: mocks.apiFetchCredentialsOnly,
}))

vi.mock('../api/profileApi', () => ({
  authTelegram: mocks.authTelegram,
}))

vi.mock('../lib/filmonySession', () => ({
  readAccessToken: mocks.readAccessToken,
  writeAccessToken: mocks.writeAccessToken,
  writeAuthSessionFlag: mocks.writeAuthSessionFlag,
}))

vi.mock('../lib/myProfileBundleCache', () => ({
  clearMyProfileBundleCache: vi.fn(),
}))

vi.mock('../lib/activityHeatmapCache', () => ({
  clearActivityHeatmapSessionCaches: vi.fn(),
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
    text: () => Promise.resolve(''),
    json: () => Promise.resolve({}),
  } as Response
}

describe('runAuthBootstrap', () => {
  let states: AuthStatus[]

  beforeEach(() => {
    states = []
    mocks.readAccessToken.mockReturnValue(null)
    mocks.apiFetch.mockReset()
    mocks.apiFetchCredentialsOnly.mockReset()
    mocks.authTelegram.mockReset()
    mocks.writeAuthSessionFlag.mockReset()
    mocks.writeAccessToken.mockReset()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('resumes with stored bearer when probe succeeds', async () => {
    mocks.readAccessToken.mockReturnValue('valid-token')
    mocks.apiFetch.mockResolvedValueOnce(mockResponse(true))
    mocks.apiFetchCredentialsOnly.mockResolvedValue(mockResponse(false, 401))

    await runAuthBootstrap({
      runId: 1,
      isCurrent: () => true,
      setState: (status) => {
        states.push(status)
      },
      waitForInitDataRaw: () => Promise.resolve('init-data'),
      environment: 'tma',
    })

    expect(states).toEqual([{ kind: 'ready' }])
    expect(mocks.writeAuthSessionFlag).toHaveBeenCalledWith(true)
    expect(mocks.authTelegram).not.toHaveBeenCalled()
  })

  it('resumes from cookie when bearer is stale but HttpOnly session is valid', async () => {
    mocks.readAccessToken.mockReturnValue('stale-token')
    mocks.apiFetch.mockResolvedValueOnce(mockResponse(false, 401))
    mocks.apiFetchCredentialsOnly.mockResolvedValueOnce(mockResponse(true))

    await runAuthBootstrap({
      runId: 1,
      isCurrent: () => true,
      setState: (status) => {
        states.push(status)
      },
      waitForInitDataRaw: () => Promise.resolve(''),
      environment: 'tma',
    })

    expect(states).toEqual([{ kind: 'ready' }])
    expect(mocks.writeAccessToken).toHaveBeenCalledWith(null)
    expect(mocks.authTelegram).not.toHaveBeenCalled()
  })

  it('falls back to authTelegram when resume probes fail', async () => {
    mocks.readAccessToken.mockReturnValue(null)
    mocks.apiFetchCredentialsOnly.mockResolvedValue(mockResponse(false, 401))
    mocks.authTelegram.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ access_token: 'fresh-token' }),
    } as Response)

    await runAuthBootstrap({
      runId: 1,
      isCurrent: () => true,
      setState: (status) => {
        states.push(status)
      },
      waitForInitDataRaw: () => Promise.resolve('telegram-init'),
      environment: 'tma',
    })

    expect(mocks.authTelegram).toHaveBeenCalledWith('telegram-init')
    expect(states).toEqual([{ kind: 'ready' }])
    expect(mocks.writeAccessToken).toHaveBeenCalledWith('fresh-token')
  })

  it('sets unauthenticated in browser when resume probes fail', async () => {
    mocks.readAccessToken.mockReturnValue(null)
    mocks.apiFetchCredentialsOnly.mockResolvedValue(mockResponse(false, 401))
    const waitForInitDataRaw = vi.fn(() => Promise.resolve(''))

    await runAuthBootstrap({
      runId: 1,
      isCurrent: () => true,
      setState: (status) => {
        states.push(status)
      },
      waitForInitDataRaw,
      environment: 'browser',
    })

    expect(states).toEqual([{ kind: 'unauthenticated' }])
    expect(waitForInitDataRaw).not.toHaveBeenCalled()
    expect(mocks.authTelegram).not.toHaveBeenCalled()
  })
})
