import { Button, Section } from '@telegram-apps/telegram-ui'
import { useQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { lazy, Suspense, useCallback, useDeferredValue, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { ApiError, formatApiDetail } from '../api/client'
import {
  getPublicProfileById,
  getUserSubscriptions,
  subscribeToUser,
  unsubscribeFromUser,
} from '../api/profileApi'
import type { MovieCardPage, PublicProfile } from '../api/profileTypes'
import {
  isDefaultRatedCardsQuery,
  ratedCardsQueryKey,
} from '../lib/ratedCardsListQuery'
import { useAuthStatus } from '../auth/useAuthStatus'
import { useTasteQuizKnowledgeOfUsers } from '../hooks/useTasteQuizKnowledgeOfUsers'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { useInfiniteScrollLoadMore } from '../hooks/useInfiniteScrollLoadMore'
import { useRatedCardsQueryFromUrl } from '../hooks/useRatedCardsQueryFromUrl'
import { useMyProfileQuery } from '../hooks/useMyProfileQuery'
import { useUserCardsInfiniteQuery } from '../hooks/useUserCardsInfiniteQuery'
import { useUserWatchlistInfiniteQuery } from '../hooks/useUserWatchlistInfiniteQuery'
import { useUserFeedPostsInfiniteQuery } from '../hooks/useUserFeedPostsInfiniteQuery'
import { useUserFavoritesStripQuery } from '../hooks/useUserFavoritesStripQuery'
import { FavoriteMoviesStrip } from '../components/profile/FavoriteMoviesStrip'
import { MoviePosterGrid } from '../components/profile/MoviePosterGrid'
import { ProfileCompactMetrics } from '../components/profile/ProfileCompactMetrics'
import { ProfileRatedCardsFilters } from '../components/profile/ProfileRatedCardsFilters'
import { ProfileHeader } from '../components/profile/ProfileHeader'
import { WatchlistPosterGrid } from '../components/profile/WatchlistPosterGrid'
import { FeedPostCard } from '../components/feed/FeedPostCard'
import { PlayfulHint } from '../components/ui/PlayfulHint'
import { InlineLoadingState } from '../components/ui/InlineLoadingState'
import {
  userCardsQueryKey,
  userFollowingStatusQueryKey,
  userPublicProfileQueryKey,
} from '../lib/profileQueryKeys'

const ProfileStatsPanel = lazy(() =>
  import('../components/profile/ProfileStatsPanel').then((m) => ({ default: m.ProfileStatsPanel })),
)

export function PublicProfilePage() {
  const { userId } = useParams<{ userId?: string }>()
  const resolvedUserId = useMemo(() => decodeURIComponent(userId ?? ''), [userId])
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [mainTab, setMainTab] = useState<'movies' | 'posts' | 'stats'>('movies')
  const [moviesSegment, setMoviesSegment] = useState<'rated' | 'watchlist'>('rated')
  const [followBusy, setFollowBusy] = useState(false)
  const [followError, setFollowError] = useState<string | null>(null)
  const [ratedQuery, setRatedQuery] = useRatedCardsQueryFromUrl()
  const deferredRatedQuery = useDeferredValue(ratedQuery)
  const ratedQueryKey = useMemo(
    () => ratedCardsQueryKey(deferredRatedQuery),
    [deferredRatedQuery],
  )

  const myProfileQuery = useMyProfileQuery()
  const myUserId = myProfileQuery.data?.id ?? null

  const profileQuery = useQuery<PublicProfile, Error>({
    queryKey: userPublicProfileQueryKey(resolvedUserId),
    queryFn: () => getPublicProfileById(resolvedUserId),
    enabled: auth.kind === 'ready' && resolvedUserId !== '',
    staleTime: 2 * 60_000,
  })

  const profile = profileQuery.data ?? null

  const followingQuery = useQuery<boolean, Error>({
    queryKey: userFollowingStatusQueryKey(myUserId ?? '', profile?.id ?? ''),
    queryFn: async () => {
      if (myUserId == null || profile == null) {
        return false
      }
      const following = await getUserSubscriptions(myUserId, 'following')
      return following.items.some((item) => item.id === profile.id)
    },
    enabled:
      auth.kind === 'ready' &&
      myUserId != null &&
      profile != null &&
      profile.id !== myUserId,
    staleTime: 60_000,
  })

  const isFollowing = followingQuery.data ?? false

  const error =
    profileQuery.error instanceof ApiError
      ? formatApiDetail(profileQuery.error.detail)
      : profileQuery.error != null
        ? profileQuery.error.message
        : null

  const cardsQuery = useUserCardsInfiniteQuery(profile?.id ?? '', ratedQuery, {
    enabled:
      auth.kind === 'ready' &&
      profile != null &&
      mainTab === 'movies' &&
      moviesSegment === 'rated',
  })

  const cards = useMemo(() => {
    const pages = cardsQuery.data?.pages
    if (pages == null || pages.length === 0) {
      return null
    }
    return {
      items: pages.flatMap((p) => p.items),
      next_cursor: pages[pages.length - 1]?.next_cursor ?? null,
    }
  }, [cardsQuery.data])

  // Product: watchlist loads eagerly on profile open (not tab-gated) so «Позже» is instant.
  const watchlistQuery = useUserWatchlistInfiniteQuery(profile?.id ?? '', {
    enabled: auth.kind === 'ready' && profile != null,
  })

  const watchlist = useMemo(() => {
    const pages = watchlistQuery.data?.pages
    if (pages == null || pages.length === 0) {
      return null
    }
    return {
      items: pages.flatMap((p) => p.items),
      next_cursor: pages[pages.length - 1]?.next_cursor ?? null,
    }
  }, [watchlistQuery.data])

  const watchlistError =
    watchlistQuery.error instanceof ApiError
      ? formatApiDetail(watchlistQuery.error.detail)
      : watchlistQuery.error != null
        ? 'Не удалось загрузить список «Позже»'
        : null

  const postsQuery = useUserFeedPostsInfiniteQuery(profile?.id ?? '', {
    enabled: auth.kind === 'ready' && profile != null && mainTab === 'posts',
  })

  const feedPosts = useMemo(() => {
    const pages = postsQuery.data?.pages
    if (pages == null || pages.length === 0) {
      return null
    }
    return {
      items: pages.flatMap((p) => p.items),
      next_cursor: pages[pages.length - 1]?.next_cursor ?? null,
    }
  }, [postsQuery.data])

  const favoritesStripQuery = useUserFavoritesStripQuery(profile?.id ?? '', {
    enabled:
      profile != null &&
      (profile.favorites_count ?? 0) > 0 &&
      mainTab === 'movies' &&
      moviesSegment === 'rated',
  })

  const favoriteStripItems = favoritesStripQuery.data ?? []

  const cardsError =
    cardsQuery.error instanceof ApiError
      ? formatApiDetail(cardsQuery.error.detail)
      : cardsQuery.error != null
        ? cardsQuery.error.message
        : null

  const ratedCardsLoading = cardsQuery.isFetching && !cardsQuery.isFetchingNextPage

  const postsErr =
    postsQuery.error instanceof ApiError
      ? formatApiDetail(postsQuery.error.detail)
      : postsQuery.error != null
        ? 'Не удалось загрузить посты'
        : null

  const postsLoading = postsQuery.isPending && postsQuery.fetchStatus === 'fetching'

  const handleFavoriteToggled = useCallback(
    (cardId: number, nextFavorite: boolean) => {
      if (profile == null) {
        return
      }
      queryClient.setQueryData<InfiniteData<MovieCardPage, string | null>>(
        userCardsQueryKey(profile.id, ratedQueryKey),
        (prev) => {
          if (prev == null) {
            return prev
          }
          return {
            ...prev,
            pages: prev.pages.map((page) => ({
              ...page,
              items: page.items.map((c) =>
                c.id === cardId ? { ...c, is_favorite: nextFavorite } : c,
              ),
            })),
          }
        },
      )
      queryClient.setQueryData<PublicProfile>(
        userPublicProfileQueryKey(resolvedUserId),
        (prev) => {
          if (prev == null) {
            return prev
          }
          return {
            ...prev,
            favorites_count: Math.max(0, prev.favorites_count + (nextFavorite ? 1 : -1)),
          }
        },
      )
    },
    [profile, queryClient, ratedQueryKey, resolvedUserId],
  )

  const drillToRatedCards = useCallback(() => {
    setMainTab('movies')
    setMoviesSegment('rated')
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        document.getElementById('profile-rated-cards-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    })
  }, [])

  const drillToWatchlist = useCallback(() => {
    setMainTab('movies')
    setMoviesSegment('watchlist')
  }, [])

  const drillToRatedSegment = useCallback(() => {
    setMainTab('movies')
    setMoviesSegment('rated')
  }, [])

  const ratedCardsLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      auth.kind === 'ready' &&
      mainTab === 'movies' &&
      moviesSegment === 'rated' &&
      Boolean(cards?.next_cursor) &&
      (cards?.items.length ?? 0) > 0,
    isBusy: cardsQuery.isFetchingNextPage,
    onLoadMore: () => void cardsQuery.fetchNextPage(),
  })

  const watchlistLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      auth.kind === 'ready' &&
      mainTab === 'movies' &&
      moviesSegment === 'watchlist' &&
      Boolean(watchlist?.next_cursor) &&
      (watchlist?.items.length ?? 0) > 0,
    isBusy: watchlistQuery.isFetchingNextPage,
    onLoadMore: () => void watchlistQuery.fetchNextPage(),
  })

  const postsLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      auth.kind === 'ready' &&
      mainTab === 'posts' &&
      Boolean(feedPosts?.next_cursor) &&
      (feedPosts?.items.length ?? 0) > 0,
    isBusy: postsQuery.isFetchingNextPage,
    onLoadMore: () => void postsQuery.fetchNextPage(),
  })

  const canLoadMore = Boolean(cards?.next_cursor)
  const canLoadMoreWatchlist = Boolean(watchlist?.next_cursor)

  async function toggleFollowing() {
    if (profile == null || myUserId == null || profile.id === myUserId) {
      return
    }
    setFollowBusy(true)
    setFollowError(null)
    try {
      if (isFollowing) {
        await unsubscribeFromUser(profile.id)
      } else {
        await subscribeToUser(profile.id)
      }
      queryClient.setQueryData<boolean>(
        userFollowingStatusQueryKey(myUserId, profile.id),
        !isFollowing,
      )
      queryClient.setQueryData<PublicProfile>(
        userPublicProfileQueryKey(resolvedUserId),
        (prev) => {
          if (prev == null || typeof prev.followers_count !== 'number') {
            return prev
          }
          return {
            ...prev,
            followers_count: Math.max(0, prev.followers_count + (isFollowing ? -1 : 1)),
          }
        },
      )
    } catch (e) {
      if (e instanceof ApiError) {
        setFollowError(formatApiDetail(e.detail))
      } else {
        setFollowError(e instanceof Error ? e.message : 'Не удалось обновить подписку')
      }
    } finally {
      setFollowBusy(false)
    }
  }

  const tasteQuizOwnerIds = useMemo(() => {
    if (profile == null || myUserId == null || profile.id === myUserId) return []
    return [profile.id]
  }, [profile, myUserId])
  const streakUserIds = useMemo(() => {
    if (profile == null) return []
    return [profile.id]
  }, [profile])
  const { knowledgeByOwnerId } = useTasteQuizKnowledgeOfUsers(tasteQuizOwnerIds, {
    enabled: tasteQuizOwnerIds.length > 0,
  })
  const { streakByUserId } = useRatingStreaksOfUsers(streakUserIds, {
    enabled: streakUserIds.length > 0,
  })

  if (auth.kind === 'loading') {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Вход…</p>
      </div>
    )
  }

  if (auth.kind === 'error') {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{auth.message}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  if (auth.kind === 'skipped') {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--hint_color)">
          Войдите через Telegram Mini App, чтобы открыть профиль.
        </p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  if (resolvedUserId === '') {
    return (
      <div className="px-4 py-10">
        <p className="filmony-text-panel text-sm text-(--tgui--hint_color)">Не указан пользователь.</p>
      </div>
    )
  }

  if (error != null) {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{error}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/profile">
          К профилю
        </Link>
      </div>
    )
  }

  if (profile == null) {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Загрузка…</p>
      </div>
    )
  }

  const isOwnPublicProfile = myUserId != null && myUserId === profile.id

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) pb-6 text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <Link
          className="flex min-h-10 min-w-10 items-center justify-center rounded-lg text-lg text-(--tgui--link_color) no-underline"
          to="/profile"
          aria-label="Назад к профилю"
        >
          ←
        </Link>
        <span className="truncate text-sm font-medium text-(--tgui--hint_color)">Профиль</span>
      </header>

      <div className="mx-auto max-w-md px-4 pt-4">
        <ProfileHeader
          profile={profile}
          subtitle=""
          viewerId={myUserId}
          knowledgeByOwnerId={knowledgeByOwnerId}
          streakByUserId={streakByUserId}
        />
        <div className="mb-4">
          <ProfileCompactMetrics
            followers_count={profile.followers_count}
            following_count={profile.following_count}
            cards_count={profile.cards_count}
            watchlist_count={profile.watchlist_count}
            favorites_count={profile.favorites_count}
            onFollowersClick={() =>
              void navigate(`/u/${encodeURIComponent(resolvedUserId)}/subscriptions?tab=followers`)
            }
            onFollowingClick={() =>
              void navigate(`/u/${encodeURIComponent(resolvedUserId)}/subscriptions?tab=following`)
            }
            onRatedClick={drillToRatedSegment}
            onWatchlistClick={drillToWatchlist}
            onFavoritesClick={drillToRatedSegment}
          />
        </div>

        {myUserId != null && profile.id !== myUserId ? (
          <div className="mb-4 flex flex-col items-center gap-2">
            {followError != null ? (
              <p className="filmony-text-panel text-center text-sm text-(--tgui--destructive_text_color)">
                {followError}
              </p>
            ) : null}
            <Button mode={isFollowing ? 'gray' : 'filled'} disabled={followBusy} onClick={() => void toggleFollowing()}>
              {followBusy ? '...' : isFollowing ? 'Отписаться' : 'Подписаться'}
            </Button>
            {isFollowing ? (
              <Button
                mode="filled"
                onClick={() => void navigate(`/taste-quiz/play/${encodeURIComponent(profile.id)}`)}
              >
                Угадать вкус
              </Button>
            ) : null}
          </div>
        ) : null}

        {profile.bio ? (
          <p className="filmony-text-panel mb-4 text-center text-sm leading-relaxed text-(--tgui--hint_color)">{profile.bio}</p>
        ) : null}

        <div className="mb-4 grid grid-cols-3 gap-1 rounded-full bg-(--tgui--secondary_bg_color) p-1">
          <button
            type="button"
            className={`flex items-center justify-center rounded-full py-2.5 text-xs font-medium transition-all sm:text-sm ${
              mainTab === 'movies'
                ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                : 'text-(--tgui--hint_color)'
            }`}
            onClick={() => setMainTab('movies')}
          >
            Карточки
          </button>
          <button
            type="button"
            className={`flex items-center justify-center rounded-full py-2.5 text-xs font-medium transition-all sm:text-sm ${
              mainTab === 'posts'
                ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                : 'text-(--tgui--hint_color)'
            }`}
            onClick={() => setMainTab('posts')}
          >
            Посты
          </button>
          <button
            type="button"
            className={`flex items-center justify-center rounded-full py-2.5 text-xs font-medium transition-all sm:text-sm ${
              mainTab === 'stats'
                ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                : 'text-(--tgui--hint_color)'
            }`}
            onClick={() => setMainTab('stats')}
          >
            Статистика
          </button>
        </div>

        {mainTab === 'movies' ? (
          <div id="profile-rated-cards-panel">
            <Section header="Карточки">
            <div className="mx-4 mb-3 flex gap-1 rounded-full bg-(--tgui--secondary_bg_color) p-1">
              <button
                type="button"
                className={`flex flex-1 items-center justify-center gap-2 rounded-full py-2.5 text-sm font-medium transition-all ${
                  moviesSegment === 'rated'
                    ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                    : 'text-(--tgui--hint_color)'
                }`}
                onClick={() => setMoviesSegment('rated')}
              >
                Оценённые
              </button>
              <button
                type="button"
                className={`flex flex-1 items-center justify-center gap-2 rounded-full py-2.5 text-sm font-medium transition-all ${
                  moviesSegment === 'watchlist'
                    ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                    : 'text-(--tgui--hint_color)'
                }`}
                onClick={() => setMoviesSegment('watchlist')}
              >
                Позже
              </button>
            </div>

            {moviesSegment === 'rated' ? (
              <>
                <FavoriteMoviesStrip items={favoriteStripItems} />
                <div className="mx-4">
                  <ProfileRatedCardsFilters
                    profileUserId={profile.id}
                    viewerUserId={myUserId}
                    cardsQuery={ratedQuery}
                    onChange={setRatedQuery}
                    enableCategoryFilter
                  />
                </div>
                {ratedCardsLoading ? (
                  <p className="filmony-text-panel mx-4 my-2 text-center text-xs text-(--tgui--hint_color)">
                    Обновляем список…
                  </p>
                ) : null}
                {cardsError != null ? (
                  <p className="filmony-text-panel mx-4 my-2 text-sm text-(--tgui--destructive_text_color)">
                    {cardsError}
                  </p>
                ) : null}
                {cards != null && cards.items.length === 0 && !ratedCardsLoading ? (
                  isDefaultRatedCardsQuery(ratedQuery) ? (
                    <PlayfulHint
                      poolKey="profile_cards_empty"
                      fallback="Пока нет карточек."
                      userId={myUserId}
                      className="filmony-text-panel mx-4 my-4 text-center text-sm text-(--tgui--hint_color)"
                    />
                  ) : (
                    <p className="filmony-text-panel mx-4 my-4 text-center text-sm text-(--tgui--hint_color)">
                      Нет карточек с такими фильтрами.
                    </p>
                  )
                ) : null}
                {cards != null && cards.items.length > 0 ? (
                  <div className="px-3 pb-3">
                    <MoviePosterGrid
                      items={cards.items}
                      showFavoriteToggle={isOwnPublicProfile}
                      onFavoriteToggled={isOwnPublicProfile ? handleFavoriteToggled : undefined}
                    />
                  </div>
                ) : null}
                {canLoadMore ? (
                  <div className="px-3 pb-3 pt-1">
                    <div ref={ratedCardsLoadMoreRef} className="h-1 w-full shrink-0" aria-hidden />
                    {cardsQuery.isFetchingNextPage ? (
                      <p className="pt-2 text-center text-xs text-(--tgui--hint_color)">Подгружаем карточки…</p>
                    ) : null}
                  </div>
                ) : null}
              </>
            ) : (
              <>
                {watchlistError != null ? (
                  <p className="filmony-text-panel mx-4 my-2 text-sm text-(--tgui--destructive_text_color)">
                    {watchlistError}
                  </p>
                ) : null}
                {watchlist != null && watchlist.items.length === 0 ? (
                  <p className="filmony-text-panel mx-4 my-4 text-center text-sm text-(--tgui--hint_color)">
                    В списке «Позже» пока пусто.
                  </p>
                ) : null}
                {watchlist != null && watchlist.items.length > 0 ? (
                  <div className="px-3 pb-3">
                    <WatchlistPosterGrid items={watchlist.items} />
                  </div>
                ) : null}
                {canLoadMoreWatchlist ? (
                  <div className="px-3 pb-3 pt-1">
                    <div ref={watchlistLoadMoreRef} className="h-1 w-full shrink-0" aria-hidden />
                    {watchlistQuery.isFetchingNextPage ? (
                      <p className="pt-2 text-center text-xs text-(--tgui--hint_color)">Подгружаем список…</p>
                    ) : null}
                  </div>
                ) : null}
              </>
            )}
          </Section>
          </div>
        ) : mainTab === 'posts' ? (
          <Section header="Посты">
            <div className="mx-4 mt-2 space-y-3 pb-3">
              {postsErr != null ? (
                <p className="text-center text-sm text-(--tgui--destructive_text_color)">{postsErr}</p>
              ) : null}
              {postsLoading ? (
                <p className="py-8 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
              ) : null}
              {!postsLoading && feedPosts != null && feedPosts.items.length === 0 ? (
                <PlayfulHint
                  poolKey="profile_posts_empty"
                  fallback="Пока нет постов в ленте"
                  userId={myUserId}
                  className="py-8 text-center text-sm text-(--tgui--hint_color)"
                />
              ) : null}
              {!postsLoading && feedPosts != null && feedPosts.items.length > 0 ? (
                <>
                  {feedPosts.items.map((post) => (
                    <FeedPostCard key={`public-profile-post-${post.id}`} post={post} viewerUserId={myUserId} />
                  ))}
                  {feedPosts.next_cursor != null && feedPosts.next_cursor !== '' ? (
                    <>
                      <div ref={postsLoadMoreRef} className="h-1 w-full shrink-0" aria-hidden />
                      {postsQuery.isFetchingNextPage ? (
                        <p className="text-center text-xs text-(--tgui--hint_color)">Подгружаем посты…</p>
                      ) : null}
                    </>
                  ) : null}
                </>
              ) : null}
            </div>
          </Section>
        ) : (
          <div className="space-y-4">
            <Suspense fallback={<InlineLoadingState message="Загрузка статистики…" />}>
              <ProfileStatsPanel
                userId={profile.id}
                cardsQuery={ratedQuery}
                onCardsQueryChange={setRatedQuery}
                enableCategoryFilter
                showPassportCollection
                onDrillToRatedCards={drillToRatedCards}
              />
            </Suspense>
          </div>
        )}
      </div>
    </div>
  )
}
