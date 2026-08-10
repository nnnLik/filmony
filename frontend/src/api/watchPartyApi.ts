import { apiFetch, apiJson, ApiError, readErrorDetail } from './client'
import type {
  WatchPartyBridgeResponse,
  WatchPartyCreateResponse,
  WatchPartyMessage,
  WatchPartyPlaybackState,
  WatchPartySlugResolve,
  WatchPartySnapshot,
} from './watchPartyTypes'

export async function createWatchParty(filmId: number): Promise<WatchPartyCreateResponse> {
  return apiJson<WatchPartyCreateResponse>('/api/watch-parties', {
    method: 'POST',
    body: JSON.stringify({ film_id: filmId }),
  })
}

export async function resolveWatchPartyBySlug(inviteSlug: string): Promise<WatchPartySlugResolve> {
  return apiJson<WatchPartySlugResolve>(`/api/watch-parties/by-slug/${encodeURIComponent(inviteSlug)}`)
}

export async function getWatchParty(partyId: string): Promise<WatchPartySnapshot> {
  return apiJson<WatchPartySnapshot>(`/api/watch-parties/${partyId}`)
}

export async function joinWatchParty(partyId: string): Promise<void> {
  const res = await apiFetch(`/api/watch-parties/${partyId}/join`, { method: 'POST' })
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorDetail(res))
  }
}

export async function leaveWatchParty(partyId: string): Promise<void> {
  const res = await apiFetch(`/api/watch-parties/${partyId}/leave`, { method: 'POST' })
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorDetail(res))
  }
}

export async function endWatchParty(partyId: string): Promise<void> {
  const res = await apiFetch(`/api/watch-parties/${partyId}/end`, { method: 'POST' })
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorDetail(res))
  }
}

export async function postWatchPartyPlayback(
  partyId: string,
  body: { action: 'play' | 'pause' | 'seek'; position_ms?: number },
): Promise<WatchPartyPlaybackState> {
  return apiJson<WatchPartyPlaybackState>(`/api/watch-parties/${partyId}/playback`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function listWatchPartyMessages(
  partyId: string,
  params?: { cursor?: number; before_id?: number; limit?: number },
): Promise<WatchPartyMessage[]> {
  const search = new URLSearchParams()
  const cursor = params?.before_id ?? params?.cursor
  if (cursor != null) {
    search.set('cursor', String(cursor))
  }
  if (params?.limit != null) {
    search.set('limit', String(params.limit))
  }
  const qs = search.toString()
  return apiJson<WatchPartyMessage[]>(
    `/api/watch-parties/${partyId}/messages${qs === '' ? '' : `?${qs}`}`,
  )
}

export async function sendWatchPartyTyping(partyId: string): Promise<void> {
  const res = await apiFetch(`/api/watch-parties/${partyId}/typing`, { method: 'POST' })
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorDetail(res))
  }
}

export async function inviteWatchPartyMembers(
  partyId: string,
  userIds: string[],
): Promise<void> {
  const res = await apiFetch(`/api/watch-parties/${partyId}/invite`, {
    method: 'POST',
    body: JSON.stringify({ user_ids: userIds }),
  })
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorDetail(res))
  }
}

export async function bridgeWatchPartyToWatchSession(
  partyId: string,
): Promise<WatchPartyBridgeResponse> {
  return apiJson<WatchPartyBridgeResponse>(`/api/watch-parties/${partyId}/bridge`, {
    method: 'POST',
  })
}

export async function createWatchPartyMessage(
  partyId: string,
  body: string,
): Promise<WatchPartyMessage> {
  return apiJson<WatchPartyMessage>(`/api/watch-parties/${partyId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ body }),
  })
}

export async function deleteWatchPartyMessage(partyId: string, messageId: number): Promise<void> {
  const res = await apiFetch(`/api/watch-parties/${partyId}/messages/${messageId}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorDetail(res))
  }
}

export async function sendWatchPartyHeartbeat(
  partyId: string,
  body?: { position_ms?: number; playing?: boolean },
): Promise<void> {
  const res = await apiFetch(`/api/watch-parties/${partyId}/heartbeat`, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorDetail(res))
  }
}
