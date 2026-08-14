import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../api/client'
import type { WatchPartySnapshot } from '../../api/watchPartyTypes'
import { useEnsureWatchParty } from '../useEnsureWatchParty'

vi.mock('../../api/watchPartyApi')

import {
  createWatchParty,
  getWatchParty,
  joinWatchParty,
  resolveWatchPartyBySlug,
} from '../../api/watchPartyApi'

function makeSnapshot(id: string, inviteSlug: string): WatchPartySnapshot {
  return {
    id,
    invite_slug: inviteSlug,
    invite_url: `https://example.com/party/${inviteSlug}`,
    status: 'active',
    film_id: 1,
    film_title: 'Test Film',
    film_poster_url: null,
    playback_iframe_url: 'https://example.com/embed',
    playback_expires_at: '2026-01-01T00:00:00Z',
    playback_state: {
      playing: false,
      position_ms: 0,
      updated_at: '2026-01-01T00:00:00Z',
      host_user_id: 'host-1',
      version: 1,
    },
    host_user_id: 'host-1',
    members: [],
    viewer_role: 'host',
    viewer_status: 'active',
  }
}

function Harness({ filmId, partySlug }: { filmId: number; partySlug: string | null }) {
  const result = useEnsureWatchParty(filmId, partySlug, true)
  return (
    <div data-testid="state">
      {result.loading ? 'loading' : result.error ?? result.snapshot?.id ?? 'none'}
    </div>
  )
}

describe('useEnsureWatchParty', () => {
  afterEach(() => {
    cleanup()
  })

  beforeEach(() => {
    vi.mocked(createWatchParty).mockReset()
    vi.mocked(getWatchParty).mockReset()
    vi.mocked(joinWatchParty).mockReset()
    vi.mocked(resolveWatchPartyBySlug).mockReset()
  })

  it('creates a party when the slug resolves to 404', async () => {
    vi.mocked(resolveWatchPartyBySlug).mockRejectedValue(new ApiError(404, 'party_not_found'))
    vi.mocked(createWatchParty).mockResolvedValue({
      id: 'p-new',
      invite_slug: 'newslug',
      invite_url: 'https://example.com/party/newslug',
    })
    vi.mocked(getWatchParty).mockResolvedValue(makeSnapshot('p-new', 'newslug'))

    render(
      <MemoryRouter>
        <Harness filmId={1} partySlug="stale-slug" />
      </MemoryRouter>,
    )

    expect(screen.getByTestId('state')).toHaveTextContent('loading')

    await waitFor(() => {
      expect(screen.getByTestId('state')).toHaveTextContent('p-new')
    })

    expect(vi.mocked(createWatchParty)).toHaveBeenCalledWith(1)
    expect(vi.mocked(getWatchParty)).toHaveBeenCalledWith('p-new')
  })

  it('creates a party when no slug is provided', async () => {
    vi.mocked(createWatchParty).mockResolvedValue({
      id: 'p-new',
      invite_slug: 'newslug',
      invite_url: 'https://example.com/party/newslug',
    })
    vi.mocked(getWatchParty).mockResolvedValue(makeSnapshot('p-new', 'newslug'))

    render(
      <MemoryRouter>
        <Harness filmId={1} partySlug={null} />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('state')).toHaveTextContent('p-new')
    })

    expect(vi.mocked(createWatchParty)).toHaveBeenCalledWith(1)
    expect(vi.mocked(resolveWatchPartyBySlug)).not.toHaveBeenCalled()
  })

  it('resolves an existing party after a 409 conflict on create', async () => {
    vi.mocked(createWatchParty).mockRejectedValue(
      new ApiError(409, {
        code: 'already_in_active_party',
        invite_slug: 'live',
        active_party_id: 'p-old',
      }),
    )
    vi.mocked(resolveWatchPartyBySlug).mockResolvedValue({
      party_id: 'p-old',
      invite_slug: 'live',
      status: 'active',
    })
    vi.mocked(getWatchParty).mockResolvedValue(makeSnapshot('p-old', 'live'))

    render(
      <MemoryRouter>
        <Harness filmId={1} partySlug={null} />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('state')).toHaveTextContent('p-old')
    })

    expect(vi.mocked(createWatchParty)).toHaveBeenCalledWith(1)
    expect(vi.mocked(resolveWatchPartyBySlug)).toHaveBeenCalledWith('live')
    expect(vi.mocked(getWatchParty)).toHaveBeenCalledWith('p-old')
  })
})
