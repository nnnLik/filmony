import { apiJson } from './client'
import type { WatchlistOverlapListResponse } from './profileTypes'

export type { WatchlistOverlapItem, WatchlistOverlapListResponse, WatchlistOverlapPartner } from './profileTypes'

export async function getMyWatchlistOverlaps(params?: {
  limit?: number
}): Promise<WatchlistOverlapListResponse> {
  const q = new URLSearchParams()
  if (params?.limit != null && params.limit >= 1) {
    q.set('limit', String(params.limit))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<WatchlistOverlapListResponse>(`/api/me/watchlist/overlaps${suffix}`)
}
