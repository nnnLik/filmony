import { apiJson } from './client'
import type { StreakBatchResponse } from './streaksTypes'

export async function batchRatingStreaks(userIds: string[]): Promise<StreakBatchResponse> {
  return apiJson<StreakBatchResponse>('/api/streaks/batch', {
    method: 'POST',
    body: JSON.stringify({
      user_ids: userIds,
    }),
  })
}
