import { ApiError, apiFetch, apiJson, readErrorDetail } from './client'
import type {
  CollectionFilmsPage,
  CollectionListResponse,
  CollectionSummary,
  ProfilePinnedCollectionsResponse,
} from './collectionsTypes'

async function assertActionOk(res: Response): Promise<void> {
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorDetail(res))
  }
}

export async function listCollections(
  params: { kind?: 'evergreen' | 'seasonal' } = {},
): Promise<CollectionListResponse> {
  const q = new URLSearchParams()
  if (params.kind != null) {
    q.set('kind', params.kind)
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<CollectionListResponse>(`/api/collections${suffix}`)
}

export async function getCollectionBySlug(slug: string): Promise<CollectionSummary> {
  return apiJson<CollectionSummary>(`/api/collections/${encodeURIComponent(slug.trim())}`)
}

export async function getCollectionFilmsPage(
  slug: string,
  params: { cursor?: string | null; limit?: number } = {},
): Promise<CollectionFilmsPage> {
  const q = new URLSearchParams()
  if (params.cursor != null && params.cursor !== '') {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<CollectionFilmsPage>(
    `/api/collections/${encodeURIComponent(slug.trim())}/films${suffix}`,
  )
}

/** @deprecated Prefer getCollectionFilmsPage */
export const listCollectionFilmsPage = getCollectionFilmsPage

export async function getProfilePinnedCollections(userId: string): Promise<ProfilePinnedCollectionsResponse> {
  return apiJson<ProfilePinnedCollectionsResponse>(
    `/api/profiles/${encodeURIComponent(userId.trim())}/collections`,
  )
}

export async function pinCollection(slug: string): Promise<void> {
  const res = await apiFetch(`/api/me/collection-pins/${encodeURIComponent(slug.trim())}`, {
    method: 'POST',
  })
  await assertActionOk(res)
}

export async function unpinCollection(slug: string): Promise<void> {
  const res = await apiFetch(`/api/me/collection-pins/${encodeURIComponent(slug.trim())}`, {
    method: 'DELETE',
  })
  await assertActionOk(res)
}
