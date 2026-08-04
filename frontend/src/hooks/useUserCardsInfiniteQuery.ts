import { useInfiniteQuery, type InfiniteData } from '@tanstack/react-query'
import { useDeferredValue, useMemo } from 'react'

import { getUserCards } from '../api/profileApi'
import type { MovieCardPage } from '../api/profileTypes'
import {
  ratedCardsQueryKey,
  ratedCardsToListParams,
  type RatedCardsListQuery,
} from '../lib/ratedCardsListQuery'
import { userCardsQueryKey } from '../lib/profileQueryKeys'

export type UseUserCardsInfiniteQueryOptions = {
  enabled?: boolean
  /** Seed first page from session bundle (own profile, default filters). */
  initialPage?: MovieCardPage | null
  initialPageUpdatedAt?: number
}

export function useUserCardsInfiniteQuery(
  userId: string,
  ratedQuery: RatedCardsListQuery,
  options?: UseUserCardsInfiniteQueryOptions,
) {
  const deferredRatedQuery = useDeferredValue(ratedQuery)
  const ratedQueryKey = useMemo(
    () => ratedCardsQueryKey(deferredRatedQuery),
    [deferredRatedQuery],
  )
  const enabledOption = options?.enabled ?? true
  const initialPage = options?.initialPage
  const initialPageUpdatedAt = options?.initialPageUpdatedAt
  const enabled = enabledOption && userId.trim() !== ''

  const initialData = useMemo((): InfiniteData<MovieCardPage, string | null> | undefined => {
    if (initialPage == null) {
      return undefined
    }
    return {
      pages: [initialPage],
      pageParams: [null],
    }
  }, [initialPage])

  return useInfiniteQuery<
    MovieCardPage,
    Error,
    InfiniteData<MovieCardPage, string | null>,
    ReturnType<typeof userCardsQueryKey>,
    string | null
  >({
    queryKey: userCardsQueryKey(userId, ratedQueryKey),
    initialPageParam: null,
    queryFn: async ({ pageParam }) => {
      return getUserCards(userId, {
        limit: 20,
        ...(pageParam != null && pageParam !== '' ? { cursor: pageParam } : {}),
        ...ratedCardsToListParams(deferredRatedQuery),
      })
    },
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled,
    staleTime: 45_000,
    gcTime: 10 * 60_000,
    initialData,
    initialDataUpdatedAt: initialPageUpdatedAt,
  })
}
