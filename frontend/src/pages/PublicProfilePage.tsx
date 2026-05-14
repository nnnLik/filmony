import { Button, Section } from '@telegram-apps/telegram-ui'
import { useCallback, useDeferredValue, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import {
  getMyProfile,
  getPublicProfileById,
  getUserCards,
  getUserFeedPosts,
  getUserSubscriptions,
  getUserWatchlist,
  subscribeToUser,
  unsubscribeFromUser,
} from '../api/profileApi'
import type { MovieCard, MovieCardPage, PublicProfile, WatchlistFilmPage } from '../api/profileTypes'
import type { UserFeedPostsPage } from '../api/feedInFeedTypes'
import {
  DEFAULT_RATED_CARDS_QUERY,
  type RatedCardsListQuery,
  isDefaultRatedCardsQuery,
  ratedCardsQueryKey,
  ratedCardsToListParams,
} from '../lib/ratedCardsListQuery'
import { useAuthStatus } from '../auth/useAuthStatus'
import { useInfiniteScrollLoadMore } from '../hooks/useInfiniteScrollLoadMore'
import { FavoriteMoviesStrip } from '../components/profile/FavoriteMoviesStrip'
import { MoviePosterGrid } from '../components/profile/MoviePosterGrid'
import { ProfileRatedCardsFilters } from '../components/profile/ProfileRatedCardsFilters'
import { ProfileHeader } from '../components/profile/ProfileHeader'
import { ProfileStatsPanel } from '../components/profile/ProfileStatsPanel'
import { WatchlistPosterGrid } from '../components/profile/WatchlistPosterGrid'
import { FeedPostCard } from '../components/feed/FeedPostCard'

function shownCount(value: number | undefined): string {
  return typeof value === 'number' ? String(value) : '0'
}

const loadMyProfile: () => Promise<{ id: string }> = getMyProfile
const loadPublicProfileById: (userId: string) => Promise<PublicProfile> = getPublicProfileById
const loadUserCards = getUserCards
const loadUserWatchlist: (
  userId: string,
  params: { cursor?: string | null; limit?: number },
) => Promise<WatchlistFilmPage> = getUserWatchlist
const loadUserSubscriptions: (
  userId: string,
  type: 'followers' | 'following' | 'both',
) => Promise<{ items: Array<{ id: string }> }> = getUserSubscriptions
const followUser: (userId: string) => Promise<void> = subscribeToUser
const unfollowUser: (userId: string) => Promise<void> = unsubscribeFromUser

export function PublicProfilePage() {
  const { userId } = useParams<{ userId?: string }>()
  const resolvedUserId = useMemo(() => decodeURIComponent(userId ?? ''), [userId])
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const [profile, setProfile] = useState<PublicProfile | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cards, setCards] = useState<MovieCardPage | null>(null)
  const [watchlist, setWatchlist] = useState<WatchlistFilmPage | null>(null)
  const [cardsError, setCardsError] = useState<string | null>(null)
  const [watchlistError, setWatchlistError] = useState<string | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)
  const [loadingMoreWatchlist, setLoadingMoreWatchlist] = useState(false)
  const [myUserId, setMyUserId] = useState<string | null>(null)
  const [isFollowing, setIsFollowing] = useState<boolean>(false)
  const [followBusy, setFollowBusy] = useState(false)
  const [feedPosts, setFeedPosts] = useState<UserFeedPostsPage | null>(null)
  const [postsLoading, setPostsLoading] = useState(false)
  const [postsErr, setPostsErr] = useState<string | null>(null)
  const [postsLoadingMore, setPostsLoadingMore] = useState(false)
  const [mainTab, setMainTab] = useState<'movies' | 'posts' | 'stats'>('movies')
  const [moviesSegment, setMoviesSegment] = useState<'rated' | 'watchlist'>('rated')
  const [favoriteStripFetched, setFavoriteStripFetched] = useState<MovieCard[]>([])
  const [favoriteStripForUserId, setFavoriteStripForUserId] = useState<string | null>(null)
  const [ratedQuery, setRatedQuery] = useState<RatedCardsListQuery>(() => ({ ...DEFAULT_RATED_CARDS_QUERY }))
  const [ratedCardsLoading, setRatedCardsLoading] = useState(false)
  const deferredRatedQuery = useDeferredValue(ratedQuery)
  const ratedQueryKey = useMemo(
    () => ratedCardsQueryKey(deferredRatedQuery),
    [deferredRatedQuery],
  )
  const favoriteStripItems = useMemo(() => {
    if (profile == null) return []
    const n = profile.favorites_count ?? 0
    if (n <= 0) return []
    if (favoriteStripForUserId !== profile.id) return []
    return favoriteStripFetched
  }, [profile, favoriteStripFetched, favoriteStripForUserId])
  const prevRouteId = useRef<string | null>(null)

  useEffect(() => {
    queueMicrotask(() => {
      setRatedQuery({ ...DEFAULT_RATED_CARDS_QUERY })
    })
  }, [resolvedUserId])

  useEffect(() => {
    if (auth.kind !== 'ready' || resolvedUserId === '') {
      return
    }
    if (prevRouteId.current != null && prevRouteId.current !== resolvedUserId) {
      setProfile(null)
      setCards(null)
      setWatchlist(null)
    }
    prevRouteId.current = resolvedUserId
    let alive = true
    void (async () => {
      await Promise.resolve()
      if (!alive) {
        return
      }
      setError(null)
      setCards(null)
      setWatchlist(null)
      setFeedPosts(null)
      setCardsError(null)
      setWatchlistError(null)
      try {
        const me = await loadMyProfile()
        if (!alive) {
          return
        }
        setMyUserId(me.id)

        const p = await loadPublicProfileById(resolvedUserId)
        if (!alive) {
          return
        }
        setProfile(p)
        if (p.id === me.id) {
          setIsFollowing(false)
        } else {
          const following = await loadUserSubscriptions(me.id, 'following')
          if (!alive) {
            return
          }
          setIsFollowing(following.items.some((item) => item.id === p.id))
        }

        try {
          const wl = await loadUserWatchlist(p.id, { limit: 20 })
          if (!alive) {
            return
          }
          setWatchlist(wl)
        } catch {
          if (!alive) {
            return
          }
          setWatchlist(null)
          setWatchlistError('Не удалось загрузить список «Позже»')
        }
      } catch (e) {
        if (!alive) {
          return
        }
        if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError(e instanceof Error ? e.message : 'Ошибка загрузки')
        }
        setProfile(null)
        setCards(null)
        setWatchlist(null)
        setFeedPosts(null)
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind, resolvedUserId])

  useEffect(() => {
    if (auth.kind !== 'ready' || profile == null || mainTab !== 'movies' || moviesSegment !== 'rated') {
      return
    }
    let alive = true
    void (async () => {
      await Promise.resolve()
      if (!alive) {
        return
      }
      setRatedCardsLoading(true)
      setCardsError(null)
      try {
        const page = await loadUserCards(profile.id, {
          limit: 20,
          ...ratedCardsToListParams(deferredRatedQuery),
        })
        if (!alive) {
          return
        }
        setCards(page)
      } catch (e) {
        if (!alive) {
          return
        }
        if (e instanceof ApiError) {
          setCardsError(formatApiDetail(e.detail))
        } else {
          setCardsError(e instanceof Error ? e.message : 'Ошибка списка')
        }
        setCards(null)
      } finally {
        if (alive) {
          setRatedCardsLoading(false)
        }
      }
    })()
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- profile.id, ratedQuery via key
  }, [auth.kind, profile?.id, mainTab, moviesSegment, ratedQueryKey])

  useEffect(() => {
    if (auth.kind !== 'ready' || profile == null || mainTab !== 'posts') {
      return
    }
    let alive = true
    void (async () => {
      setPostsLoading(true)
      setPostsErr(null)
      try {
        const page = await getUserFeedPosts(profile.id, { limit: 20 })
        if (!alive) return
        setFeedPosts(page)
      } catch (e) {
        if (!alive) return
        setPostsErr(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить посты')
        setFeedPosts(null)
      } finally {
        if (alive) setPostsLoading(false)
      }
    })()
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- profile.id достаточно
  }, [auth.kind, profile?.id, mainTab])

  useEffect(() => {
    if (profile == null) {
      return
    }
    const n = profile.favorites_count ?? 0
    if (n <= 0) {
      return
    }
    let alive = true
    void (async () => {
      try {
        const page = await loadUserCards(profile.id, { favoritesOnly: true, limit: 30 })
        if (!alive) {
          return
        }
        setFavoriteStripFetched(page.items)
        setFavoriteStripForUserId(profile.id)
      } catch {
        if (alive) {
          setFavoriteStripFetched([])
          setFavoriteStripForUserId(profile.id)
        }
      }
    })()
    return () => {
      alive = false
    }
  }, [profile])

  const loadMoreCards = useCallback(async () => {
    if (profile == null || cards?.next_cursor == null || cards.next_cursor === '') {
      return
    }
    setLoadingMore(true)
    setCardsError(null)
    try {
      const page = await loadUserCards(profile.id, {
        cursor: cards.next_cursor,
        limit: 20,
        ...ratedCardsToListParams(deferredRatedQuery),
      })
      setCards((prev) => {
        if (prev == null) {
          return page
        }
        return {
          items: [...prev.items, ...page.items],
          next_cursor: page.next_cursor,
        }
      })
    } catch (e) {
      if (e instanceof ApiError) {
        setCardsError(formatApiDetail(e.detail))
      } else {
        setCardsError(e instanceof Error ? e.message : 'Ошибка списка')
      }
    } finally {
      setLoadingMore(false)
    }
  }, [profile, cards, deferredRatedQuery])

  const loadMoreWatchlist = useCallback(async () => {
    if (profile == null || watchlist?.next_cursor == null || watchlist.next_cursor === '') {
      return
    }
    setLoadingMoreWatchlist(true)
    setWatchlistError(null)
    try {
      const page = await loadUserWatchlist(profile.id, { cursor: watchlist.next_cursor, limit: 20 })
      setWatchlist((prev) => {
        if (prev == null) {
          return page
        }
        return {
          items: [...prev.items, ...page.items],
          next_cursor: page.next_cursor,
        }
      })
    } catch (e) {
      if (e instanceof ApiError) {
        setWatchlistError(formatApiDetail(e.detail))
      } else {
        setWatchlistError(e instanceof Error ? e.message : 'Ошибка списка')
      }
    } finally {
      setLoadingMoreWatchlist(false)
    }
  }, [profile, watchlist])

  const loadMorePosts = useCallback(async () => {
    if (profile == null || feedPosts?.next_cursor == null || feedPosts.next_cursor === '') {
      return
    }
    setPostsLoadingMore(true)
    setPostsErr(null)
    try {
      const page = await getUserFeedPosts(profile.id, { cursor: feedPosts.next_cursor, limit: 20 })
      setFeedPosts((prev) => {
        if (prev == null) return page
        return {
          items: [...prev.items, ...page.items],
          next_cursor: page.next_cursor,
        }
      })
    } catch (e) {
      if (e instanceof ApiError) {
        setPostsErr(formatApiDetail(e.detail))
      } else {
        setPostsErr(e instanceof Error ? e.message : 'Ошибка загрузки')
      }
    } finally {
      setPostsLoadingMore(false)
    }
  }, [profile, feedPosts])

  const handleFavoriteToggled = useCallback((cardId: number, nextFavorite: boolean) => {
    setCards((prev) => {
      if (prev == null) {
        return prev
      }
      return {
        ...prev,
        items: prev.items.map((c) => (c.id === cardId ? { ...c, is_favorite: nextFavorite } : c)),
      }
    })
    setProfile((p) => {
      if (p == null) {
        return p
      }
      return {
        ...p,
        favorites_count: Math.max(0, p.favorites_count + (nextFavorite ? 1 : -1)),
      }
    })
  }, [])

  const ratedCardsLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      auth.kind === 'ready' &&
      mainTab === 'movies' &&
      moviesSegment === 'rated' &&
      Boolean(cards?.next_cursor) &&
      (cards?.items.length ?? 0) > 0,
    isBusy: loadingMore,
    onLoadMore: () => void loadMoreCards(),
  })

  const watchlistLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      auth.kind === 'ready' &&
      mainTab === 'movies' &&
      moviesSegment === 'watchlist' &&
      Boolean(watchlist?.next_cursor) &&
      (watchlist?.items.length ?? 0) > 0,
    isBusy: loadingMoreWatchlist,
    onLoadMore: () => void loadMoreWatchlist(),
  })

  const postsLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      auth.kind === 'ready' &&
      mainTab === 'posts' &&
      Boolean(feedPosts?.next_cursor) &&
      (feedPosts?.items.length ?? 0) > 0,
    isBusy: postsLoadingMore,
    onLoadMore: () => void loadMorePosts(),
  })

  const canLoadMore = Boolean(cards?.next_cursor)
  const canLoadMoreWatchlist = Boolean(watchlist?.next_cursor)

  async function toggleFollowing() {
    if (profile == null || myUserId == null || profile.id === myUserId) {
      return
    }
    setFollowBusy(true)
    try {
      if (isFollowing) {
        await unfollowUser(profile.id)
      } else {
        await followUser(profile.id)
      }
      setIsFollowing((prev) => !prev)
      setProfile((prev) => {
        if (prev == null) {
          return prev
        }
        if (typeof prev.followers_count !== 'number') {
          return prev
        }
        return {
          ...prev,
          followers_count: Math.max(0, prev.followers_count + (isFollowing ? -1 : 1)),
        }
      })
    } catch (e) {
      if (e instanceof ApiError) {
        setError(formatApiDetail(e.detail))
      } else {
        setError(e instanceof Error ? e.message : 'Не удалось обновить подписку')
      }
    } finally {
      setFollowBusy(false)
    }
  }

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
        />
        <div className="mb-4 grid grid-cols-2 gap-2">
          <button
            type="button"
            className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center transition-opacity active:opacity-80"
            onClick={() =>
              void navigate(`/u/${encodeURIComponent(resolvedUserId)}/subscriptions?tab=followers`)
            }
          >
            <span className="block text-xl font-semibold tabular-nums">{shownCount(profile.followers_count)}</span>
            <span className="text-[11px] text-(--tgui--hint_color)">подписчиков</span>
          </button>
          <button
            type="button"
            className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center transition-opacity active:opacity-80"
            onClick={() =>
              void navigate(`/u/${encodeURIComponent(resolvedUserId)}/subscriptions?tab=following`)
            }
          >
            <span className="block text-xl font-semibold tabular-nums">{shownCount(profile.following_count)}</span>
            <span className="text-[11px] text-(--tgui--hint_color)">подписок</span>
          </button>
          <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center">
            <span className="block text-xl font-semibold tabular-nums">{shownCount(profile.cards_count)}</span>
            <span className="text-[11px] text-(--tgui--hint_color)">оценено</span>
          </div>
          <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center">
            <span className="block text-xl font-semibold tabular-nums">{shownCount(profile.watchlist_count)}</span>
              <span className="text-[11px] text-(--tgui--hint_color)">позже</span>
          </div>
          <div className="col-span-2 rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center">
            <span className="block text-xl font-semibold tabular-nums">{shownCount(profile.favorites_count)}</span>
            <span className="text-[11px] text-(--tgui--hint_color)">в любимых</span>
          </div>
        </div>

        {myUserId != null && profile.id !== myUserId ? (
          <div className="mb-4 flex justify-center">
            <Button mode={isFollowing ? 'gray' : 'filled'} disabled={followBusy} onClick={() => void toggleFollowing()}>
              {followBusy ? '...' : isFollowing ? 'Отписаться' : 'Подписаться'}
            </Button>
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
                    cardsQuery={ratedQuery}
                    onChange={setRatedQuery}
                    enableCategoryFilter={isOwnPublicProfile}
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
                {cards != null && cards.items.length === 0 && !loadingMore && !ratedCardsLoading ? (
                  <p className="filmony-text-panel mx-4 my-4 text-center text-sm text-(--tgui--hint_color)">
                    {isDefaultRatedCardsQuery(ratedQuery) ? 'Пока нет карточек.' : 'Нет карточек с такими фильтрами.'}
                  </p>
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
                    {loadingMore ? (
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
                    {loadingMoreWatchlist ? (
                      <p className="pt-2 text-center text-xs text-(--tgui--hint_color)">Подгружаем список…</p>
                    ) : null}
                  </div>
                ) : null}
              </>
            )}
          </Section>
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
                <p className="py-8 text-center text-sm text-(--tgui--hint_color)">Пока нет постов в ленте</p>
              ) : null}
              {!postsLoading && feedPosts != null && feedPosts.items.length > 0 ? (
                <>
                  {feedPosts.items.map((post) => (
                    <FeedPostCard key={`public-profile-post-${post.id}`} post={post} viewerUserId={myUserId} />
                  ))}
                  {feedPosts.next_cursor != null && feedPosts.next_cursor !== '' ? (
                    <>
                      <div ref={postsLoadMoreRef} className="h-1 w-full shrink-0" aria-hidden />
                      {postsLoadingMore ? (
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
            <ProfileStatsPanel userId={profile.id} />
          </div>
        )}
      </div>
    </div>
  )
}
