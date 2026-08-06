import { useInfiniteQuery, type InfiniteData } from '@tanstack/react-query'
import { useMemo } from 'react'

import { getCollectionFilmsPage } from '../api/collectionsApi'
import type { CollectionFilmsPage } from '../api/collectionsTypes'
import { collectionFilmsQueryKey } from '../lib/collectionQueryKeys'

import { useAuthReadyGate } from './useAuthReadyGate'

export function useCollectionFilmsInfinite(
  slug: string,
  options: { enabled?: boolean; limit?: number } = {},
) {
  const { isAuthReady } = useAuthReadyGate()
  const { enabled = true, limit = 25 } = options

  const query = useInfiniteQuery<
    CollectionFilmsPage,
    Error,
    InfiniteData<CollectionFilmsPage, string | null>,
    ReturnType<typeof collectionFilmsQueryKey>,
    string | null
  >({
    queryKey: collectionFilmsQueryKey(slug),
    queryFn: ({ pageParam }) =>
      getCollectionFilmsPage(slug, { cursor: pageParam ?? null, limit }),
    initialPageParam: null,
    getNextPageParam: (lastPage) => lastPage.next_cursor,
    enabled: isAuthReady && slug.trim() !== '' && enabled,
    staleTime: 45_000,
  })

  const films = useMemo(
    () => query.data?.pages.flatMap((page) => page.items) ?? [],
    [query.data],
  )

  const totalCount = query.data?.pages[0]?.total_count ?? null

  return { ...query, films, totalCount }
}
