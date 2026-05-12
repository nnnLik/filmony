import { Button, IconButton } from '@telegram-apps/telegram-ui'
import { PenLine, UserRoundX } from 'lucide-react'
import { useInfiniteQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { useInfiniteScrollLoadMore } from '../hooks/useInfiniteScrollLoadMore'
import { Link, useLocation, useNavigate } from 'react-router-dom'

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
import { FeedTopFab } from '../components/feed/FeedTopFab'
import { RecentCardsStrip } from '../components/feed/RecentCardsStrip'
import {
  MY_PROFILE_BUNDLE_CHANGED_EVENT,
  readMyProfileBundleCache,
} from '../lib/myProfileBundleCache'
import { globalFeedQueryKey, myMovieCardTagStatsQueryKey } from '../feed/feedQueryKeys'
import { writeCachedMyMovieCardTagStats } from '../lib/movieCardTagStatsStorage'
import { greetingFirstName } from '../lib/profileDisplay'
import { readRecentCardViews } from '../lib/recentCardViews'
import { readFeedScrollSnapshot, saveFeedScrollSnapshot } from '../lib/feedScrollRestore'
import { consumeGlobalFeedHeadSse } from '../lib/globalFeedSse'
import {
  isGlobalFeedCardDetailOpened,
  isGlobalFeedPostDetailOpened,
} from '../lib/globalFeedViewedIds'
import { readGlobalFeedHideMine, writeGlobalFeedHideMine } from '../lib/globalFeedHideMine'

const FEED_KIND_TABS: Array<{ value: GlobalFeedKind; segmentLabel: string }> = [
  { value: 'all', segmentLabel: 'Всё' },
  { value: 'posts', segmentLabel: 'Посты' },
  { value: 'cards', segmentLabel: 'Карточки' },
]

export function FeedPage() {
  const auth = useAuthStatus()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const location = useLocation()
  const { openCompose } = useComposeFeedPost()
  const pendingScrollYRef = useRef<number | null>(null)
  const feedKindRef = useRef<GlobalFeedKind>('all')

  const [feedKind, setFeedKind] = useState<GlobalFeedKind>('all')
  const [myProfileBundle, setMyProfileBundle] = useState(() => readMyProfileBundleCache())
  const viewerUserId = myProfileBundle?.profile.id ?? null
  const [hideMine, setHideMine] = useState(() => {
    if (typeof window === 'undefined') return false
    const uid = readMyProfileBundleCache()?.profile.id ?? null
    return readGlobalFeedHideMine(uid)
  })
  const emptyFeedGreeting = greetingFirstName(myProfileBundle?.profile)

  const [recentStrip, setRecentStrip] = useState(() => {
    const uid = readMyProfileBundleCache()?.profile.id
    return uid != null ? readRecentCardViews(uid) : []
  })

  const [liveHeadVersion, setLiveHeadVersion] = useState(0)
  const [ackHeadVersion, setAckHeadVersion] = useState(0)

  useEffect(() => {
    feedKindRef.current = feedKind
  }, [feedKind])

  useEffect(() => {
    queueMicrotask(() => {
      setHideMine(readGlobalFeedHideMine(viewerUserId))
    })
  }, [viewerUserId])

  useEffect(() => {
    if (auth.kind !== 'ready') {
      return
    }
    let timeoutId: number | undefined
    const onScroll = () => {
      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId)
      }
      timeoutId = window.setTimeout(() => {
        saveFeedScrollSnapshot(feedKindRef.current, window.scrollY)
      }, 200)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      window.removeEventListener('scroll', onScroll)
      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [auth.kind])

  useEffect(() => {
    const st = location.state as { restoreFeedScroll?: boolean } | undefined
    if (!st?.restoreFeedScroll || auth.kind !== 'ready') {
      return
    }
    const snapshot = readFeedScrollSnapshot()
    void navigate('.', { replace: true, state: {} })
    queueMicrotask(() => {
      if (snapshot != null) {
        setFeedKind(snapshot.kind)
        pendingScrollYRef.current = snapshot.y
      }
    })
  }, [location.state, navigate, auth.kind])

  const refreshRecentStrip = useCallback(() => {
    const uid = readMyProfileBundleCache()?.profile.id
    setRecentStrip(uid != null ? readRecentCardViews(uid) : [])
  }, [])

  const refreshProfileBundle = useCallback(() => {
    setMyProfileBundle(readMyProfileBundleCache())
  }, [])

  const excludeOwn = auth.kind === 'ready' && hideMine

  const feedQuery = useInfiniteQuery({
    queryKey: globalFeedQueryKey(feedKind, excludeOwn),
    initialPageParam: null as string | null,
    queryFn: async ({ pageParam }) =>
      getGlobalFeedPage({
        limit: 20,
        kind: feedKind,
        excludeOwn,
        ...(pageParam != null && pageParam !== '' ? { cursor: pageParam } : {}),
      }),
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled: auth.kind === 'ready',
    staleTime: 2 * 60_000,
    gcTime: 60 * 60_000,
  })

  useEffect(() => {
    const p0 = feedQuery.data?.pages[0]
    if (p0 == null) return
    const v = p0.feed_head_version ?? 0
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

  const items = useMemo(
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

  const onCommentsState = useCallback(
    (cardId: number, next: { comments_count: number; comments_preview: MovieCardComment[] }) => {
      const key = globalFeedQueryKey(feedKind, excludeOwn)
      queryClient.setQueryData<InfiniteData<FeedMovieCardPage, string | null>>(key, (old) => {
        if (old == null) return old
        return {
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
              return { ...entry, ...next }
            }),
          })),
        }
      })
    },
    [queryClient, feedKind, excludeOwn],
  )

  const onFeedPostCommentsState = useCallback(
    (postId: number, next: { comments_count: number; comments_preview: FeedPostComment[] }) => {
      const key = globalFeedQueryKey(feedKind, excludeOwn)
      queryClient.setQueryData<InfiniteData<FeedMovieCardPage, string | null>>(key, (old) => {
        if (old == null) return old
        return {
          ...old,
          pages: old.pages.map((page) => ({
            ...page,
            items: page.items.map((entry) => {
              if (entry.kind !== 'feed_post' || entry.id !== postId) {
                return entry
              }
              return { ...entry, ...next }
            }),
          })),
        }
      })
    },
    [queryClient, feedKind, excludeOwn],
  )

  const onToggleHideMine = useCallback(() => {
    setHideMine((prev) => {
      const next = !prev
      writeGlobalFeedHideMine(viewerUserId, next)
      return next
    })
  }, [viewerUserId])

  useEffect(() => {
    const y = pendingScrollYRef.current
    if (y == null) return
    if (auth.kind !== 'ready') return
    if (feedQuery.isPending && items.length === 0) return

    pendingScrollYRef.current = null
    window.requestAnimationFrame(() => {
      window.scrollTo({ top: y, behavior: 'auto' })
    })
  }, [auth.kind, feedQuery.isPending, items.length, feedKind])

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
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="px-4 pb-3 pt-3">
          <div className="mb-3 flex items-center gap-2">
            <h1 className="min-w-0 flex-1 truncate bg-linear-to-r from-(--filmony-mint,#5eead4) via-(--filmony-text,#e8f0f7) to-(--filmony-amber,#e8b86d) bg-clip-text text-lg font-semibold tracking-tight text-transparent">
              Лента
            </h1>
            <div className="flex shrink-0 items-center gap-1">
              {auth.kind === 'ready' ? (
                <IconButton
                  type="button"
                  mode={hideMine ? 'bezeled' : 'gray'}
                  size="s"
                  onClick={onToggleHideMine}
                  aria-label={hideMine ? 'Показывать в ленте мои посты и карточки' : 'Скрыть из ленты мои посты и карточки'}
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
                <IconButton
                  type="button"
                  mode="gray"
                  size="s"
                  onClick={() => openCompose()}
                  aria-label="Новый пост в ленту"
                  title="Пост в ленту"
                >
                  <PenLine className="block size-[18px]" strokeWidth={2} />
                </IconButton>
              ) : null}
              <Link to="/cards/new" aria-label="Добавить карточку" className="shrink-0 no-underline">
                <Button mode="gray">+</Button>
              </Link>
            </div>
          </div>
          <div
            className="flex w-full rounded-xl bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] p-0.5"
            role="tablist"
            aria-label="Тип ленты"
          >
            {FEED_KIND_TABS.map((entry) => {
              const selected = feedKind === entry.value
              return (
                <button
                  key={entry.value}
                  type="button"
                  role="tab"
                  aria-selected={selected}
                  className={`min-w-0 flex-1 truncate rounded-lg px-1.5 py-2 text-[13px] font-medium transition active:scale-[0.99] ${
                    selected
                      ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-[0_1px_2px_rgba(0,0,0,0.12)]'
                      : 'text-(--tgui--hint_color)'
                  }`}
                  onClick={() => setFeedKind(entry.value)}
                >
                  {entry.segmentLabel}
                </button>
              )
            })}
          </div>
          <p className="mt-2 text-[12px] leading-snug text-(--tgui--hint_color)">
            Публичная лента приложения по времени публикации.
          </p>
        </div>
      </header>

      <RecentCardsStrip items={recentStrip} />

      <main className="max-w-full overflow-x-hidden px-4 pb-10 pt-3">
        <div className="flex flex-col gap-5">
          {(authPending || showSkeleton) && items.length === 0 && (
            <div className="flex flex-col gap-4">
              <FeedCardSkeleton />
              <FeedCardSkeleton />
              <FeedCardSkeleton />
            </div>
          )}

          {!authPending && errorMessage != null && items.length === 0 && (
            <div className="rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] px-4 py-4">
              <p className="text-[14px] text-(--tgui--hint_color)">{errorMessage}</p>
              <Button stretched className="mt-4" onClick={() => void feedQuery.refetch()}>
                Повторить
              </Button>
            </div>
          )}

          {!authPending && errorMessage == null && items.length === 0 && !showSkeleton && (
            <div className="flex flex-col items-center gap-4 rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] px-4 py-10">
              <p className="text-center text-[14px] leading-relaxed text-(--tgui--hint_color)">
                {emptyFeedGreeting != null
                  ? `${emptyFeedGreeting}, здесь пока пусто`
                  : 'Здесь появятся публичные посты и карточки пользователей.'}
              </p>
              <Link to="/cards/new" className="w-full no-underline">
                <Button stretched>Добавить карточку</Button>
              </Link>
            </div>
          )}

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
                        viewerUserId={viewerUserId}
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
                      viewerUserId={viewerUserId}
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
    </div>
  )
}
