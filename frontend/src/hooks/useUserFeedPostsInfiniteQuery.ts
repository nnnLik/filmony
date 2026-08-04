import { useInfiniteQuery, type InfiniteData } from '@tanstack/react-query'

import { getUserFeedPosts } from '../api/profileApi'
import type { UserFeedPostsPage } from '../api/feedInFeedTypes'
import { userFeedPostsQueryKey } from '../lib/profileQueryKeys'

export type UseUserFeedPostsInfiniteQueryOptions = {
  enabled?: boolean
}

export function useUserFeedPostsInfiniteQuery(
  userId: string,
  options?: UseUserFeedPostsInfiniteQueryOptions,
) {
  const enabled = (options?.enabled ?? true) && userId.trim() !== ''

  return useInfiniteQuery<
    UserFeedPostsPage,
    Error,
    InfiniteData<UserFeedPostsPage, string | null>,
    ReturnType<typeof userFeedPostsQueryKey>,
    string | null
  >({
    queryKey: userFeedPostsQueryKey(userId),
    initialPageParam: null,
    queryFn: async ({ pageParam }) => {
      return getUserFeedPosts(userId, {
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
