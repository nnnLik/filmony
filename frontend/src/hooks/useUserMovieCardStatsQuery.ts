import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { getUserMovieCardStats } from '../api/profileApi'
import type { UserMovieCardStats } from '../api/profileTypes'
import { userMovieCardStatsQueryKey } from '../lib/profileQueryKeys'

export type UseUserMovieCardStatsQueryOptions = {
  enabled?: boolean
}

export function useUserMovieCardStatsQuery(
  userId: string,
  activityCategoryId: number | null,
  options?: UseUserMovieCardStatsQueryOptions,
) {
  const enabled = (options?.enabled ?? true) && userId.trim() !== ''

  return useQuery<UserMovieCardStats, Error>({
    queryKey: userMovieCardStatsQueryKey(userId, activityCategoryId),
    queryFn: () => getUserMovieCardStats(userId, { activityCategoryId }),
    enabled,
    staleTime: 45_000,
    gcTime: 10 * 60_000,
    placeholderData: keepPreviousData,
  })
}
