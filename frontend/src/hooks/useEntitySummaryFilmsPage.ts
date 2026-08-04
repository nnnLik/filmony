import { useInfiniteQuery, type QueryKey } from '@tanstack/react-query'
import { useMemo } from 'react'

import { useAuthReadyGate } from './useAuthReadyGate'
import type { CursorPage } from './useCursorInfiniteList'

type UseEntitySummaryFilmsPageOptions<TFilm, TQueryKey extends QueryKey> = {
  queryKey: TQueryKey
  fetchPage: (params: { cursor: string | null; limit: number }) => Promise<CursorPage<TFilm>>
  entityReady: boolean
  summaryReady: boolean
  limit?: number
  staleTime?: number
}

export function useEntitySummaryFilmsPage<TFilm, TQueryKey extends QueryKey>({
  queryKey,
  fetchPage,
  entityReady,
  summaryReady,
  limit = 20,
  staleTime = 45_000,
}: UseEntitySummaryFilmsPageOptions<TFilm, TQueryKey>) {
  const { isAuthReady } = useAuthReadyGate()

  const query = useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam }) => fetchPage({ cursor: pageParam ?? null, limit }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor,
    enabled: isAuthReady && entityReady && summaryReady,
    staleTime,
  })

  const films = useMemo(
    () => query.data?.pages.flatMap((page) => page.items) ?? [],
    [query.data],
  )

  return { ...query, films }
}
