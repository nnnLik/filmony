import { Button, IconButton } from '@telegram-apps/telegram-ui'
import { UserRoundX } from 'lucide-react'
import { useInfiniteQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useRef, useState, type ComponentProps } from 'react'

import { useInfiniteScrollLoadMore } from '../hooks/useInfiniteScrollLoadMore'
import { useLocation, type Location } from 'react-router'

import { useComposeFeedPost } from '../compose/useComposeFeedPost'

import { getGlobalFeedPage } from '../api/cardApi'
import { ApiError, formatApiDetail } from '../api/client'
import { getMyMovieCardTagStats } from '../api/profileApi'
import { useAuthStatus } from '../auth/useAuthStatus'
import type { FeedMovieCardPage } from '../api/feedListPageTypes'
import type { FeedPostComment, GlobalFeedKind, MovieCardComment } from '../api/profileTypes'
import { FeedCard } from '../components/feed/FeedCard'
import { FeedPostCard } from '../components/feed/FeedPostCard'
import { FeedCardSkeleton } from '../components/feed/FeedCardSkeleton'
import { CreateActionSheet } from '../components/feed/CreateActionSheet'
import { FeedTopFab } from '../components/feed/FeedTopFab'
import { RecentCardsStrip } from '../components/feed/RecentCardsStrip'
import { PageHeader } from '../components/layout/PageHeader'
import { EmptyState } from '../components/ui/EmptyState'
import { MicroFunToast } from '../components/ui/MicroFunToast'
import { ListErrorState } from '../components/ui/ListErrorState'
import { SegmentedControl } from '../components/ui/SegmentedControl'
import {
  MY_PROFILE_BUNDLE_CHANGED_EVENT,
  readMyProfileBundleCache,
} from '../lib/myProfileBundleCache'
import { globalFeedQueryKey, myMovieCardTagStatsQueryKey } from '../feed/feedQueryKeys'
import { formatOfflineCacheTimestamp } from '../lib/formatOfflineCacheTimestamp'
import {
  readCachedGlobalFeedPage,
  writeCachedGlobalFeedPage,
} from '../lib/globalFeedCacheStorage'
import { writeCachedMyMovieCardTagStats } from '../lib/movieCardTagStatsStorage'
import { greetingFirstName } from '../lib/profileDisplay'
import { readRecentCardViews } from '../lib/recentCardViews'
import { FeedCardGlobalAudioProvider } from '../context/FeedCardGlobalAudioProvider'
import { consumeGlobalFeedHeadSse } from '../lib/globalFeedSse'
import {
  isGlobalFeedCardDetailOpened,
  isGlobalFeedPostDetailOpened,
} from '../lib/globalFeedViewedIds'
import { readGlobalFeedHideMine, writeGlobalFeedHideMine } from '../lib/globalFeedHideMine'
import { scheduleDeferredPepeDancingPrewarm } from '../lib/pepeGif'
import { useFeedScrollDepthSecret } from '../hooks/useFeedScrollDepthSecret'
import { buildRouteKey, registerScrollContainer } from '../features/scrollRestore'

import './FeedPage.css'

type GreetingProfile = Parameters<typeof greetingFirstName>[0]
type GreetingProfileWithId = GreetingProfile & { id: number }
const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null

const buildRouteKeySafe = buildRouteKey as (loc: Location, keys: string[]) => string
const registerScrollContainerSafe = registerScrollContainer as (
  key: string,
  container: HTMLElement,
) => void | (() => void)

const isGreetingProfile = (value: unknown): value is GreetingProfile => isRecord(value)
const hasGreetingProfileId = (
  value: GreetingProfile | null | undefined,
): value is GreetingProfileWithId =>
  isRecord(value) && typeof (value as Record<string, unknown>).id === 'number'

const getProfileFromBundle = (bundle: unknown): GreetingProfile | null => {
  if (!isRecord(bundle)) return null
  const profile = bundle.profile
  if (!isGreetingProfile(profile)) return null
  return profile
}

const readViewerUserIdFromCache = () => {
  const bundle: unknown = readMyProfileBundleCache()
  const profile = getProfileFromBundle(bundle)
  return hasGreetingProfileId(profile) ? profile.id : null
}

const FEED_KIND_TABS: Array<{ value: GlobalFeedKind; segmentLabel: string }> = [
  { value: 'all', segmentLabel: 'Всё' },
  { value: 'posts', segmentLabel: 'Посты' },
  { value: 'cards', segmentLabel: 'Карточки' },
]

type RecentCardsStripItems = ComponentProps<typeof RecentCardsStrip>['items']
const getEmptyRecentStrip = (): RecentCardsStripItems => []

export function FeedPage() {
  const auth = useAuthStatus()
  const queryClient = useQueryClient()
  const location = useLocation()
  const { openCompose } = useComposeFeedPost()
  const scrollContainerRef = useRef<HTMLElement | null>(null)

  const [createSheetOpen, setCreateSheetOpen] = useState(false)
  const [feedKind, setFeedKind] = useState<GlobalFeedKind>('all')
  const [myProfileBundle, setMyProfileBundle] = useState<unknown>(() => {
    const bundle: unknown = readMyProfileBundleCache()
    return bundle
  })
  const profile = useMemo(() => getProfileFromBundle(myProfileBundle), [myProfileBundle])
  const viewerUserId = hasGreetingProfileId(profile) ? profile.id : null
  const viewerUserIdString = viewerUserId != null ? String(viewerUserId) : null
  const [hideMine, setHideMine] = useState(() => {
    if (typeof window === 'undefined') return false
    const uid = readViewerUserIdFromCache()
    return readGlobalFeedHideMine(uid != null ? String(uid) : null)
  })
  const emptyFeedGreeting = greetingFirstName(profile ?? undefined)

  const [recentStrip, setRecentStrip] = useState<RecentCardsStripItems>(() => {
    const uid = readViewerUserIdFromCache()
    return uid != null ? readRecentCardViews(String(uid)) : getEmptyRecentStrip()
  })

  const [liveHeadVersion, setLiveHeadVersion] = useState(0)
  const [ackHeadVersion, setAckHeadVersion] = useState(0)
  const [offlineCacheStoredAt, setOfflineCacheStoredAt] = useState<number | null>(null)
  const routeKey = useMemo(() => buildRouteKeySafe(location, ['q', 'filter']), [location])

  useEffect(() => {
    scheduleDeferredPepeDancingPrewarm()
  }, [])

  useEffect(() => {
    queueMicrotask(() => {
      setHideMine(readGlobalFeedHideMine(viewerUserIdString))
    })
  }, [viewerUserIdString])

  const refreshRecentStrip = useCallback(() => {
    const uid = readViewerUserIdFromCache()
    setRecentStrip(uid != null ? readRecentCardViews(String(uid)) : getEmptyRecentStrip())
  }, [])

  const refreshProfileBundle = useCallback(() => {
    setMyProfileBundle(readMyProfileBundleCache())
  }, [])

  const excludeOwn = auth.kind === 'ready' && hideMine

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
      const response = await getGlobalFeedPage({
        limit: 20,
        kind: feedKind,
        excludeOwn,
        ...(pageParam != null && pageParam !== '' ? { cursor: pageParam } : {}),
      })
      return response
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

  useEffect(() => {
    const container = scrollContainerRef.current
    if (!container) return undefined
    return registerScrollContainerSafe(routeKey, container)
  }, [routeKey])

  useEffect(() => {
    if (auth.kind !== 'ready') {
      return
    }
    void queryClient.prefetchQuery({
      queryKey: myMovieCardTagStatsQueryKey(),
      queryFn: async () => {
        const res = await getMyMovieCardTagStats()
        writeCachedMyMovieCardTagStats(res)
        return res
      },
      staleTime: 2 * 60_000,
    })
  }, [auth.kind, queryClient])

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

  const { toastMessage, dismissToast } = useFeedScrollDepthSecret({
    containerRef: scrollContainerRef,
    userId: viewerUserIdString,
    enabled: auth.kind === 'ready' && errorMessage == null,
    itemCount: items.length,
    hasNextPage,
    isFetchingNextPage: feedQuery.isFetchingNextPage,
  })

  useEffect(() => {
    void Promise.resolve().then(() => {
      refreshRecentStrip()
      refreshProfileBundle()
    })
    const onVis = () => {
      if (document.visibilityState === 'visible') {
        refreshRecentStrip()
        refreshProfileBundle()
      }
    }
    const onRecent = () => refreshRecentStrip()
    const onProfile = () => refreshProfileBundle()
    document.addEventListener('visibilitychange', onVis)
    window.addEventListener('filmony-recent-cards-changed', onRecent)
    window.addEventListener(MY_PROFILE_BUNDLE_CHANGED_EVENT, onProfile)
    return () => {
      document.removeEventListener('visibilitychange', onVis)
      window.removeEventListener('filmony-recent-cards-changed', onRecent)
      window.removeEventListener(MY_PROFILE_BUNDLE_CHANGED_EVENT, onProfile)
    }
  }, [refreshRecentStrip, refreshProfileBundle])

  const showOfflineStaleBanner =
    offlineCacheStoredAt != null &&
    items.length > 0 &&
    (feedQuery.isError || (feedQuery.isFetching && !feedQuery.isFetchedAfterMount))

  const onCommentsState = useCallback(
    (cardId: number, nextState: { comments_count: number; comments_preview: MovieCardComment[] }) => {
      const key = globalFeedQueryKey(feedKind, excludeOwn)
      queryClient.setQueryData<InfiniteData<FeedMovieCardPage, string | null>>(key, (old) => {
        if (old == null) return old
        const updated: InfiniteData<FeedMovieCardPage, string | null> = {
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
        }
        if (viewerUserIdString != null) {
          void writeCachedGlobalFeedPage(viewerUserIdString, feedKind, excludeOwn, updated)
        }
        return updated
      })
    },
    [queryClient, feedKind, excludeOwn, viewerUserIdString],
  )

  const onFeedPostCommentsState = useCallback(
    (postId: number, nextState: { comments_count: number; comments_preview: FeedPostComment[] }) => {
      const key = globalFeedQueryKey(feedKind, excludeOwn)
      queryClient.setQueryData<InfiniteData<FeedMovieCardPage, string | null>>(key, (old) => {
        if (old == null) return old
        const next = {
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
        }
        if (viewerUserIdString != null) {
          void writeCachedGlobalFeedPage(viewerUserIdString, feedKind, excludeOwn, next)
        }
        return next
      })
    },
    [queryClient, feedKind, excludeOwn, viewerUserIdString],
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

  if (auth.kind === 'error') {
    return (
      <div className="min-h-full px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{auth.message}</p>
        <p className="mt-3 text-sm text-(--tgui--hint_color)">Обновите страницу или откройте мини-приложение снова из Telegram.</p>
      </div>
    )
  }

  if (auth.kind === 'skipped') {
    return (
      <div className="min-h-full px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--hint_color)">
          Откройте приложение в Telegram, чтобы увидеть ленту.
        </p>
      </div>
    )
  }

  const authPending = auth.kind === 'loading'

  return (
    <FeedCardGlobalAudioProvider>
    <div className="min-h-full">
      <PageHeader
        title="Лента"
        pepeClassName="feed-page__title-pepe"
        actions={
          <>
            {auth.kind === 'ready' ? (
              <IconButton
                type="button"
                mode={hideMine ? 'bezeled' : 'gray'}
                size="s"
                onClick={onToggleHideMine}
                aria-label={
                  hideMine
                    ? 'Показывать в ленте мои посты и карточки'
                    : 'Скрыть из ленты мои посты и карточки'
                }
                aria-pressed={hideMine}
                title={
                  hideMine
                    ? 'Показать мои посты и карточки на этой вкладке'
                    : 'Скрыть мои посты и карточки на этой вкладке'
                }
              >
                <UserRoundX className="block size-[18px]" strokeWidth={2} />
              </IconButton>
            ) : null}
            {auth.kind === 'ready' ? (
              <Button mode="gray" size="s" onClick={() => setCreateSheetOpen(true)}>
                Создать
              </Button>
            ) : null}
          </>
        }
        tabs={
          <SegmentedControl
            value={feedKind}
            onChange={setFeedKind}
            ariaLabel="Тип ленты"
            segments={FEED_KIND_TABS.map((entry) => ({
              value: entry.value,
              label: entry.segmentLabel,
            }))}
          />
        }
        subtitle={
          <p className="mt-2 text-[12px] leading-snug text-(--tgui--hint_color)">
            Публичная лента приложения по времени публикации.
          </p>
        }
      />

      <RecentCardsStrip items={recentStrip} />

      <main
        ref={scrollContainerRef}
        data-route-key={routeKey}
        className="max-w-full overflow-x-hidden px-4 pb-10 pt-3"
      >
        <div className="flex flex-col gap-5">
          {(authPending || showSkeleton) && items.length === 0 && (
            <div className="flex flex-col gap-4">
              <FeedCardSkeleton />
              <FeedCardSkeleton />
              <FeedCardSkeleton />
            </div>
          )}

          {!authPending && errorMessage != null && items.length === 0 && (
            <ListErrorState
              message={errorMessage}
              onRetry={() => {
                void feedQuery.refetch()
              }}
            />
          )}

          {!authPending && errorMessage == null && items.length === 0 && !showSkeleton && (
            <EmptyState
              message={
                emptyFeedGreeting != null
                  ? 'здесь пока пусто'
                  : 'Здесь появятся публичные посты и карточки пользователей.'
              }
              playfulKey="feed_empty"
              playfulSeedUserId={viewerUserIdString}
              playfulMessagePrefix={
                emptyFeedGreeting != null ? `${emptyFeedGreeting}, ` : undefined
              }
              action={
                auth.kind === 'ready'
                  ? { label: 'Создать', onClick: () => setCreateSheetOpen(true) }
                  : undefined
              }
            />
          )}

          {showOfflineStaleBanner ? (
            <div className="rounded-xl border border-(--tgui--separator_color) bg-(--tgui--secondary_bg_color) px-3 py-2 text-[12px] leading-snug text-(--tgui--hint_color)">
              Данные от {formatOfflineCacheTimestamp(offlineCacheStoredAt)}.
              {feedQuery.isError ? (
                <>
                  {' '}
                  <button
                    type="button"
                    className="text-(--tgui--link_color) underline-offset-2 hover:underline"
                    onClick={() => {
                      void feedQuery.refetch()
                    }}
                  >
                    Обновить
                  </button>
                </>
              ) : null}
            </div>
          ) : null}

          {items.length > 0 && (
            <>
              {items.map((entry) => {
                if (entry.kind === 'feed_post') {
                  const dim = isGlobalFeedPostDetailOpened(entry.id)
                  return (
                    <div
                      key={`post-${entry.id}`}
                      className={dim ? 'opacity-[0.88]' : undefined}
                    >
                      <FeedPostCard
                        post={entry}
                        viewerUserId={viewerUserIdString}
                        onCommentsState={onFeedPostCommentsState}
                      />
                    </div>
                  )
                }
                const dimC = isGlobalFeedCardDetailOpened(entry.id)
                return (
                  <div key={`card-${entry.id}`} className={dimC ? 'opacity-[0.88]' : undefined}>
                    <FeedCard
                      card={entry}
                      viewerUserId={viewerUserIdString}
                      onCommentsState={onCommentsState}
                    />
                  </div>
                )
              })}
              {hasNextPage ? (
                <>
                  <div
                    ref={feedLoadMoreSentinelRef}
                    className="h-1 w-full shrink-0"
                    aria-hidden
                  />
                  {feedQuery.isFetchingNextPage ? (
                    <p className="pb-4 pt-2 text-center text-xs text-(--tgui--hint_color)">Подгружаем ленту…</p>
                  ) : null}
                </>
              ) : null}
            </>
          )}
        </div>
      </main>

      {auth.kind === 'ready' ? (
        <FeedTopFab
          liveHeadVersion={liveHeadVersion}
          ackHeadVersion={ackHeadVersion}
          onRefetch={onRefetchFeed}
        />
      ) : null}

      {createSheetOpen ? (
        <CreateActionSheet
          onClose={() => setCreateSheetOpen(false)}
          onOpenCompose={() => openCompose()}
        />
      ) : null}

      <MicroFunToast message={toastMessage} onDismiss={dismissToast} />
    </div>
    </FeedCardGlobalAudioProvider>
  )
}
