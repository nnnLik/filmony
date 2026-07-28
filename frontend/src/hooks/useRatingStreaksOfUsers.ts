import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import { batchRatingStreaks } from '../api/streaksApi'
import {
  STREAK_BATCH_MAX_USER_IDS,
  type StreakBatchItem,
  type StreakBatchResponse,
} from '../api/streaksTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { ratingStreaksOfUsersQueryKey } from '../lib/streaksQueryKeys'

export type UseRatingStreaksOfUsersOptions = {
  enabled?: boolean
}

function normalizeUserIds(userIds: readonly string[]): string[] {
  const unique = [...new Set(userIds.filter((id) => id.trim() !== ''))]
  return unique.slice(0, STREAK_BATCH_MAX_USER_IDS).sort()
}

/**
 * Batch rating streaks for displayed users. API returns only entries with current ≥ 4.
 *
 * Return shape: `streakByUserId` maps user id → `{ current }`.
 */
export function useRatingStreaksOfUsers(
  userIds: readonly string[],
  options?: UseRatingStreaksOfUsersOptions,
) {
  const auth = useAuthStatus()
  const sortedIds = useMemo(() => normalizeUserIds(userIds), [userIds])

  const enabled = (options?.enabled ?? true) && auth.kind === 'ready' && sortedIds.length > 0

  const query = useQuery<StreakBatchResponse, Error>({
    queryKey: ratingStreaksOfUsersQueryKey(sortedIds),
    queryFn: () => batchRatingStreaks(sortedIds),
    enabled,
  })

  const streakByUserId: Record<string, StreakBatchItem> = query.data?.items ?? {}

  return {
    ...query,
    streakByUserId,
  }
}
