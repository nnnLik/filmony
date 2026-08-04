import { useInfiniteQuery, type InfiniteData } from '@tanstack/react-query'

import { getUserWatchlist } from '../api/profileApi'
import type { WatchlistEntryPage } from '../api/profileTypes'
import { userWatchlistQueryKey } from '../lib/profileQueryKeys'

export type UseUserWatchlistInfiniteQueryOptions = {
  enabled?: boolean
}

export function useUserWatchlistInfiniteQuery(
  userId: string,
  options?: UseUserWatchlistInfiniteQueryOptions,
) {
  const enabled = (options?.enabled ?? true) && userId.trim() !== ''

  return useInfiniteQuery<
    WatchlistEntryPage,
    Error,
    InfiniteData<WatchlistEntryPage, string | null>,
    ReturnType<typeof userWatchlistQueryKey>,
    string | null
  >({
    queryKey: userWatchlistQueryKey(userId),
    initialPageParam: null,
    queryFn: async ({ pageParam }) => {
      return getUserWatchlist(userId, {
        limit: 20,
        ...(pageParam != null && pageParam !== '' ? { cursor: pageParam } : {}),
      })
    },
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled,
    staleTime: 45_000,
    gcTime: 10 * 60_000,
  })
}
