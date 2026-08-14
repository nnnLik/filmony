import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from './client'
import { inviteWatchPartyMembers } from './watchPartyApi'

describe('inviteWatchPartyMembers', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('posts JSON with Content-Type application/json', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    await inviteWatchPartyMembers('party-1', ['user-a'])

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/api/watch-parties/party-1/invite')
    const headers = init.headers as Record<string, string>
    expect(headers['Content-Type']).toBe('application/json')
    expect(init.body).toEqual(JSON.stringify({ user_ids: ['user-a'] }))
  })

  it('throws ApiError when the API returns 422', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Input should be a valid dictionary or object to extract fields from' }), {
        status: 422,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(inviteWatchPartyMembers('party-1', ['user-a'])).rejects.toSatisfy((err: unknown) => {
      return err instanceof ApiError && err.status === 422
    })
  })
})
