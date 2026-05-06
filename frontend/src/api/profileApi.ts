import { apiFetch, apiJson } from './client'
import type { MovieCardPage, MyProfile, PublicProfile } from './profileTypes'

export async function getMyProfile(): Promise<MyProfile> {
  return apiJson<MyProfile>('/api/me/profile')
}

export async function patchMyProfile(body: {
  display_name?: string | null
  bio?: string | null
  profile_slug?: string | null
}): Promise<MyProfile> {
  return apiJson<MyProfile>('/api/me/profile', {
    method: 'PATCH',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}

export async function getPublicProfileById(userId: string): Promise<PublicProfile> {
  return apiJson<PublicProfile>(`/api/users/${encodeURIComponent(userId)}`)
}

export async function getPublicProfileBySlug(slug: string): Promise<PublicProfile> {
  return apiJson<PublicProfile>(`/api/users/by-slug/${encodeURIComponent(slug)}`)
}

export async function getUserCards(
  userId: string,
  params: { cursor?: string | null; limit?: number },
): Promise<MovieCardPage> {
  const q = new URLSearchParams()
  if (params.cursor) {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<MovieCardPage>(`/api/users/${encodeURIComponent(userId)}/cards${suffix}`)
}

export async function authTelegram(initData: string): Promise<Response> {
  return apiFetch('/api/auth/telegram', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ initData }),
  })
}
