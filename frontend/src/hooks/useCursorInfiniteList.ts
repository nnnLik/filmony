import { useInfiniteQuery, type QueryKey } from '@tanstack/react-query'
import { useMemo } from 'react'

import { useAuthReadyGate } from './useAuthReadyGate'

export type CursorPage<TItem> = {
  items: TItem[]
  next_cursor: string | null
}

type UseCursorInfiniteListOptions<TItem, TQueryKey extends QueryKey> = {
  queryKey: TQueryKey
  queryFn: (params: { cursor: string | null; limit: number }) => Promise<CursorPage<TItem>>
  enabled?: boolean
  limit?: number
  staleTime?: number
}

export function useCursorInfiniteList<TItem, TQueryKey extends QueryKey>({
  queryKey,
  queryFn,
  enabled = true,
  limit = 50,
  staleTime = 60_000,
}: UseCursorInfiniteListOptions<TItem, TQueryKey>) {
  const { isAuthReady } = useAuthReadyGate()

  const query = useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam }) => queryFn({ cursor: pageParam ?? null, limit }),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor,
    enabled: isAuthReady && enabled,
    staleTime,
  })

  const items = useMemo(
    () => query.data?.pages.flatMap((page) => page.items) ?? [],
    [query.data],
  )

  return { ...query, items }
}
