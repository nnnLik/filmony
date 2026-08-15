import { useQuery } from '@tanstack/react-query'

import { getUserActivityHeatmap } from '../api/profileApi'
import type { UserActivityHeatmap } from '../api/profileTypes'
import {
  readCachedUserActivityHeatmap,
  writeCachedUserActivityHeatmap,
} from '../lib/activityHeatmapCache'
import { profileQueryRootKey } from '../lib/profileQueryKeys'

export const userActivityHeatmapQueryKey = (
  userId: string,
  activityCategoryId: number | null,
) => [...profileQueryRootKey, 'activityHeatmap', userId, activityCategoryId] as const

export type UseUserActivityHeatmapQueryOptions = {
  enabled?: boolean
}

export function useUserActivityHeatmapQuery(
  userId: string,
  activityCategoryId: number | null,
  options?: UseUserActivityHeatmapQueryOptions,
) {
  const enabled = (options?.enabled ?? true) && userId.trim() !== ''

  return useQuery<UserActivityHeatmap, Error>({
    queryKey: userActivityHeatmapQueryKey(userId, activityCategoryId),
    queryFn: async () => {
      const data = await getUserActivityHeatmap(userId, { activityCategoryId })
      if (activityCategoryId == null) {
        writeCachedUserActivityHeatmap(userId, data)
      }
      return data
    },
    enabled,
    staleTime: 45_000,
    gcTime: activityCategoryId == null ? 10 * 60_000 : 90_000,
    placeholderData: (previous) =>
      previous ??
      (activityCategoryId == null ? (readCachedUserActivityHeatmap(userId) ?? undefined) : undefined),
  })
}
