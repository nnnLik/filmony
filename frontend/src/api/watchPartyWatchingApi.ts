import { apiJson } from './client'
import type { FollowingWatchingNowResponse, WatchingNowBatchResponse } from './watchPartyTypes'

export async function batchWatchingNow(userIds: string[]): Promise<WatchingNowBatchResponse> {
  return apiJson<WatchingNowBatchResponse>('/api/watch-parties/watching/batch', {
    method: 'POST',
    body: JSON.stringify({ user_ids: userIds }),
  })
}

export async function getFollowingWatchingNow(): Promise<FollowingWatchingNowResponse> {
  return apiJson<FollowingWatchingNowResponse>('/api/watch-parties/watching/following')
}
