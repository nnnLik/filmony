import {
  useInfiniteQuery,
  useQueryClient,
  type InfiniteData,
  type UseInfiniteQueryResult,
} from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { getGlobalFeedPage, getMovieCardFeedPage } from '../api/cardApi'
import { ApiError, formatApiDetail } from '../api/client'
import type { FeedMovieCardPage } from '../api/feedListPageTypes'
import type { FeedPostComment, GlobalFeedKind, MovieCardComment } from '../api/profileTypes'
import type { AuthStatus } from '../auth/auth-context'
import { globalFeedQueryKey } from '../feed/feedQueryKeys'
import {
  readCachedGlobalFeedPage,
  writeCachedGlobalFeedPage,
} from '../lib/globalFeedCacheStorage'
import { readGlobalFeedHideMine, writeGlobalFeedHideMine } from '../lib/globalFeedHideMine'
import { consumeGlobalFeedHeadSse } from '../lib/globalFeedSse'
import {
  readMyProfileBundleCache,
} from '../lib/myProfileBundleCache'
import { useInfiniteScrollLoadMore } from './useInfiniteScrollLoadMore'

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null

const readViewerUserIdFromCache = (): string | null => {
  const bundle: unknown = readMyProfileBundleCache()
  if (!isRecord(bundle)) return null
  const profile = bundle.profile
  if (!isRecord(profile) || typeof profile.id !== 'number') return null
  return String(profile.id)
}

export type UseGlobalFeedOptions = {
  auth: AuthStatus
  viewerUserIdString: string | null
}

export type UseGlobalFeedResult = {
  feedKind: GlobalFeedKind
  setFeedKind: (kind: GlobalFeedKind) => void
  hideMine: boolean
  onToggleHideMine: () => void
  excludeOwn: boolean
  isPersonalFeed: boolean
  items: FeedMovieCardPage['items']
  feedQuery: UseInfiniteQueryResult<
    InfiniteData<FeedMovieCardPage, string | null>,
    Error
  >
  hasNextPage: boolean
  showSkeleton: boolean
  errorMessage: string | null
  feedLoadMoreSentinelRef: ReturnType<typeof useInfiniteScrollLoadMore>
  liveHeadVersion: number
  ackHeadVersion: number
  offlineCacheStoredAt: number | null
  showOfflineStaleBanner: boolean
  onCommentsState: (
    cardId: number,
    nextState: { comments_count: number; comments_preview: MovieCardComment[] },
  ) => void
  onFeedPostCommentsState: (
    postId: number,
    nextState: { comments_count: number; comments_preview: FeedPostComment[] },
  ) => void
  onFeedPostDeleted: (postId: number) => void
  onRefetchFeed: () => Promise<void>
}

export function useGlobalFeed({
  auth,
  viewerUserIdString,
}: UseGlobalFeedOptions): UseGlobalFeedResult {
  const queryClient = useQueryClient()

  const [feedKind, setFeedKind] = useState<GlobalFeedKind>('for_you')
  const isPersonalFeed = feedKind === 'for_you'
  const [hideMine, setHideMine] = useState(() => {
    if (typeof window === 'undefined') return false
    const uid = readViewerUserIdFromCache()
    return readGlobalFeedHideMine(uid)
  })
  const [liveHeadVersion, setLiveHeadVersion] = useState(0)
  const [ackHeadVersion, setAckHeadVersion] = useState(0)
  const [offlineCacheStoredAt, setOfflineCacheStoredAt] = useState<number | null>(null)

  const excludeOwn = auth.kind === 'ready' && hideMine

  useEffect(() => {
    queueMicrotask(() => {
      setHideMine(readGlobalFeedHideMine(viewerUserIdString))
    })
  }, [viewerUserIdString])

  useEffect(() => {
    if (viewerUserIdString == null) {
      queueMicrotask(() => {
        setOfflineCacheStoredAt(null)
      })
      return
    }
    let cancelled = false
    void readCachedGlobalFeedPage(viewerUserIdString, feedKind, excludeOwn).then((blob) => {
      if (cancelled || blob == null) {
        return
      }
      queryClient.setQueryData<InfiniteData<FeedMovieCardPage, string | null>>(
        globalFeedQueryKey(feedKind, excludeOwn),
        blob.payload,
      )
      queueMicrotask(() => {
        setOfflineCacheStoredAt(blob.storedAt)
      })
    })
    return () => {
      cancelled = true
    }
  }, [viewerUserIdString, feedKind, excludeOwn, queryClient])

  const feedQuery = useInfiniteQuery<
    FeedMovieCardPage,
    Error,
    InfiniteData<FeedMovieCardPage, string | null>,
    ReturnType<typeof globalFeedQueryKey>,
    string | null
  >({
    queryKey: globalFeedQueryKey(feedKind, excludeOwn),
    initialPageParam: null,
    queryFn: async ({ pageParam }) => {
      if (feedKind === 'for_you') {
        return getMovieCardFeedPage({
          limit: 20,
          ...(pageParam != null && pageParam !== '' ? { cursor: pageParam } : {}),
        })
      }
      return getGlobalFeedPage({
        limit: 20,
        kind: feedKind,
        excludeOwn,
        ...(pageParam != null && pageParam !== '' ? { cursor: pageParam } : {}),
      })
    },
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled: auth.kind === 'ready',
    staleTime: 2 * 60_000,
    gcTime: 60 * 60_000,
  })

  useEffect(() => {
    if (
      viewerUserIdString == null ||
      !feedQuery.isSuccess ||
      feedQuery.data?.pages[0] == null
    ) {
      return
    }
    queueMicrotask(() => {
      setOfflineCacheStoredAt(null)
    })
    void writeCachedGlobalFeedPage(
      viewerUserIdString,
      feedKind,
      excludeOwn,
      feedQuery.data,
    )
  }, [
    viewerUserIdString,
    feedKind,
    excludeOwn,
    feedQuery.isSuccess,
    feedQuery.data,
    feedQuery.dataUpdatedAt,
  ])

  useEffect(() => {
    const p0 = feedQuery.data?.pages[0]
    if (p0 == null) return
    const v = typeof p0.feed_head_version === 'number' ? p0.feed_head_version : 0
    queueMicrotask(() => {
      setAckHeadVersion((prev) => Math.max(prev, v))
      setLiveHeadVersion((prev) => Math.max(prev, v))
    })
  }, [feedQuery.data?.pages, feedQuery.dataUpdatedAt])

  useEffect(() => {
    if (auth.kind !== 'ready') return
    const ac = new AbortController()
    void consumeGlobalFeedHeadSse(ac.signal, (v) => {
      setLiveHeadVersion((prev) => Math.max(prev, v))
    }).catch(() => {})
    return () => ac.abort()
  }, [auth.kind])

  const items = useMemo<FeedMovieCardPage['items']>(
    () => feedQuery.data?.pages.flatMap((p) => p.items) ?? [],
    [feedQuery.data],
  )

  const hasNextPage = Boolean(feedQuery.hasNextPage)
  const showSkeleton =
    auth.kind === 'loading' || (feedQuery.isPending && feedQuery.fetchStatus === 'fetching')

  const errorMessage =
    feedQuery.isError && feedQuery.error instanceof ApiError
      ? formatApiDetail(feedQuery.error.detail)
      : feedQuery.isError
        ? feedQuery.error instanceof Error
          ? feedQuery.error.message
          : 'Не удалось загрузить ленту'
        : null

  const feedLoadMoreSentinelRef = useInfiniteScrollLoadMore({
    enabled:
      auth.kind === 'ready' && hasNextPage && items.length > 0 && errorMessage == null,
    isBusy: feedQuery.isFetchingNextPage,
    onLoadMore: () => {
      void feedQuery.fetchNextPage()
    },
  })

  const showOfflineStaleBanner =
    offlineCacheStoredAt != null &&
    items.length > 0 &&
    (feedQuery.isError || (feedQuery.isFetching && !feedQuery.isFetchedAfterMount))

  const updateFeedCache = useCallback(
    (
      updater: (
        old: InfiniteData<FeedMovieCardPage, string | null>,
      ) => InfiniteData<FeedMovieCardPage, string | null>,
    ) => {
      const key = globalFeedQueryKey(feedKind, excludeOwn)
      queryClient.setQueryData<InfiniteData<FeedMovieCardPage, string | null>>(key, (old) => {
        if (old == null) return old
        const next = updater(old)
        if (viewerUserIdString != null) {
          void writeCachedGlobalFeedPage(viewerUserIdString, feedKind, excludeOwn, next)
        }
        return next
      })
    },
    [queryClient, feedKind, excludeOwn, viewerUserIdString],
  )

  const onCommentsState = useCallback(
    (cardId: number, nextState: { comments_count: number; comments_preview: MovieCardComment[] }) => {
      updateFeedCache((old) => ({
        ...old,
        pages: old.pages.map((page) => ({
          ...page,
          items: page.items.map((entry) => {
            if (entry.kind === 'feed_post') {
              return entry
            }
            if (entry.id !== cardId) {
              return entry
            }
            return { ...entry, ...nextState }
          }),
        })),
      }))
    },
    [updateFeedCache],
  )

  const onFeedPostCommentsState = useCallback(
    (postId: number, nextState: { comments_count: number; comments_preview: FeedPostComment[] }) => {
      updateFeedCache((old) => ({
        ...old,
        pages: old.pages.map((page) => ({
          ...page,
          items: page.items.map((entry) => {
            if (entry.kind !== 'feed_post' || entry.id !== postId) {
              return entry
            }
            return { ...entry, ...nextState }
          }),
        })),
      }))
    },
    [updateFeedCache],
  )

  const onFeedPostDeleted = useCallback(
    (postId: number) => {
      updateFeedCache((old) => ({
        ...old,
        pages: old.pages.map((page) => ({
          ...page,
          items: page.items.filter((entry) => entry.kind !== 'feed_post' || entry.id !== postId),
        })),
      }))
    },
    [updateFeedCache],
  )

  const onToggleHideMine = useCallback(() => {
    setHideMine((prev) => {
      const next = !prev
      writeGlobalFeedHideMine(viewerUserIdString, next)
      return next
    })
  }, [viewerUserIdString])

  const onRefetchFeed = useCallback(async () => {
    await feedQuery.refetch()
  }, [feedQuery])

  return {
    feedKind,
    setFeedKind,
    hideMine,
    onToggleHideMine,
    excludeOwn,
    isPersonalFeed,
    items,
    feedQuery,
    hasNextPage,
    showSkeleton,
    errorMessage,
    feedLoadMoreSentinelRef,
    liveHeadVersion,
    ackHeadVersion,
    offlineCacheStoredAt,
    showOfflineStaleBanner,
    onCommentsState,
    onFeedPostCommentsState,
    onFeedPostDeleted,
    onRefetchFeed,
  }
}
