import { apiJson } from './client'
import type { WatchingNowBatchResponse } from './watchPartyTypes'

export async function batchWatchingNow(userIds: string[]): Promise<WatchingNowBatchResponse> {
  return apiJson<WatchingNowBatchResponse>('/api/watch-parties/watching/batch', {
    method: 'POST',
    body: JSON.stringify({ user_ids: userIds }),
  })
}
