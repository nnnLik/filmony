import { Button } from '@telegram-apps/telegram-ui'
import { useInfiniteQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { useInfiniteScrollLoadMore } from '../hooks/useInfiniteScrollLoadMore'
import { Link } from 'react-router-dom'

import { getMovieCardFeedPage } from '../api/cardApi'
import { ApiError, formatApiDetail } from '../api/client'
import { getMyMovieCardTagStats } from '../api/profileApi'
import { useAuthStatus } from '../auth/useAuthStatus'
import type {
  FeedListMode,
  FeedMovieCard,
  FeedMovieCardPage,
  MovieCardComment,
} from '../api/profileTypes'
import { FeedCard } from '../components/feed/FeedCard'
import { FeedCardSkeleton } from '../components/feed/FeedCardSkeleton'
import { FEED_MODE_ENTRIES, feedModeHint } from '../components/feed/feedModePickerConstants'
import { RecentCardsStrip } from '../components/feed/RecentCardsStrip'
import {
  MY_PROFILE_BUNDLE_CHANGED_EVENT,
  readMyProfileBundleCache,
} from '../lib/myProfileBundleCache'
import { movieCardFeedQueryKey, myMovieCardTagStatsQueryKey } from '../feed/feedQueryKeys'
import { writeCachedMyMovieCardTagStats } from '../lib/movieCardTagStatsStorage'
import { greetingFirstName } from '../lib/profileDisplay'
import { readRecentCardViews } from '../lib/recentCardViews'

export function FeedPage() {
  const auth = useAuthStatus()
  const queryClient = useQueryClient()

  const [feedMode, setFeedMode] = useState<FeedListMode>('default')
  const [myProfileBundle, setMyProfileBundle] = useState(() => readMyProfileBundleCache())
  const viewerUserId = myProfileBundle?.profile.id ?? null
  const emptyFeedGreeting = greetingFirstName(myProfileBundle?.profile)

  const [recentStrip, setRecentStrip] = useState(() => {
    const uid = readMyProfileBundleCache()?.profile.id
    return uid != null ? readRecentCardViews(uid) : []
  })

  const refreshRecentStrip = useCallback(() => {
    const uid = readMyProfileBundleCache()?.profile.id
    setRecentStrip(uid != null ? readRecentCardViews(uid) : [])
  }, [])

  const refreshProfileBundle = useCallback(() => {
    setMyProfileBundle(readMyProfileBundleCache())
  }, [])

  const feedQuery = useInfiniteQuery({
    queryKey: movieCardFeedQueryKey(feedMode),
    initialPageParam: null as string | null,
    queryFn: async ({ pageParam }) =>
      getMovieCardFeedPage({
        limit: 20,
        mode: feedMode,
        ...(pageParam != null && pageParam !== '' ? { cursor: pageParam } : {}),
      }),
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled: auth.kind === 'ready',
    staleTime: 2 * 60_000,
    gcTime: 60 * 60_000,
  })

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
      const key = movieCardFeedQueryKey(feedMode)
      queryClient.setQueryData<InfiniteData<FeedMovieCardPage, string | null>>(key, (old) => {
        if (old == null) return old
        return {
          ...old,
          pages: old.pages.map((page) => ({
            ...page,
            items: page.items.map((c) => (c.id === cardId ? { ...c, ...next } : c)),
          })),
        }
      })
    },
    [queryClient, feedMode],
  )

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
            <div className="flex shrink-0 items-center gap-1.5">
              <Link to="/cards/new" aria-label="Добавить карточку" className="shrink-0 no-underline">
                <Button mode="gray">+</Button>
              </Link>
            </div>
          </div>
          <div
            className="flex w-full rounded-xl bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] p-0.5"
            role="tablist"
            aria-label="Источник ленты"
          >
            {FEED_MODE_ENTRIES.map((entry) => {
              const selected = feedMode === entry.value
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
                  onClick={() => setFeedMode(entry.value)}
                >
                  {entry.segmentLabel}
                </button>
              )
            })}
          </div>
          <p className="mt-2 text-[12px] leading-snug text-(--tgui--hint_color)">{feedModeHint(feedMode)}</p>
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
                  ? `${emptyFeedGreeting}, добавь первую карточку`
                  : 'Добавь первую карточку — здесь появятся оценки друзей и рекомендации.'}
              </p>
              <Link to="/cards/new" className="w-full no-underline">
                <Button stretched>Добавить карточку</Button>
              </Link>
            </div>
          )}

          {items.length > 0 && (
            <>
              {items.map((card: FeedMovieCard) => (
                <FeedCard
                  key={card.id}
                  card={card}
                  viewerUserId={viewerUserId}
                  onCommentsState={onCommentsState}
                />
              ))}
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
    </div>
  )
}
