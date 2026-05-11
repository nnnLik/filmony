import { Avatar, Button, IconButton, Title } from '@telegram-apps/telegram-ui'
import { Download } from 'lucide-react'
import { useCallback, useDeferredValue, useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { ApiError, formatApiDetail } from '../api/client'
import { getMyProfile, getUserCards, getUserFeedPosts, getUserWatchlist, postExportMyCardsCsv } from '../api/profileApi'
import type {
  MovieCard,
  MovieCardPage,
  MyProfile,
  PublicProfile,
  UserFeedPostsPage,
  WatchlistFilmPage,
} from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { FavoriteMoviesStrip } from '../components/profile/FavoriteMoviesStrip'
import { MoviePosterGrid } from '../components/profile/MoviePosterGrid'
import { ProfileRatedCardsFilters } from '../components/profile/ProfileRatedCardsFilters'
import { ProfileStatsPanel } from '../components/profile/ProfileStatsPanel'
import { WatchlistPosterGrid } from '../components/profile/WatchlistPosterGrid'
import { FeedPostCard } from '../components/feed/FeedPostCard'
import { readMyProfileBundleCache, writeMyProfileBundleCache } from '../lib/myProfileBundleCache'
import {
  DEFAULT_RATED_CARDS_QUERY,
  type RatedCardsListQuery,
  isDefaultRatedCardsQuery,
  ratedCardsQueryKey,
  ratedCardsToListParams,
} from '../lib/ratedCardsListQuery'
import { displayNameFromProfile, profileInitials } from '../lib/profileDisplay'
import {
  isTelegramChatUnavailableDetail,
  notificationFailureMessage,
  openTelegramDeepLink,
  telegramBotOpenUrl,
} from '../lib/telegramNotificationError'
import { useInfiniteScrollLoadMore } from '../hooks/useInfiniteScrollLoadMore'

type ProfileMainTab = 'movies' | 'posts' | 'stats'

function shownCount(value: number | undefined): string {
  return typeof value === 'number' ? String(value) : '0'
}

function toPublicShape(p: MyProfile): PublicProfile {
  return {
    id: p.id,
    profile_slug: p.profile_slug,
    username: p.username,
    first_name: p.first_name,
    last_name: p.last_name,
    photo_url: p.photo_url,
    display_name: p.display_name,
    bio: p.bio,
    cards_count: p.cards_count,
    favorites_count: p.favorites_count,
    watchlist_count: p.watchlist_count,
    friends_count: p.friends_count,
    followers_count: p.followers_count,
    following_count: p.following_count,
  }
}

export function ProfilePage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const location = useLocation()
  const initialBundle = useMemo(() => readMyProfileBundleCache(), [])

  const [mainTab, setMainTab] = useState<ProfileMainTab>('movies')
  const [profile, setProfile] = useState<MyProfile | null>(() => initialBundle?.profile ?? null)
  const [myCards, setMyCards] = useState<MovieCardPage | null>(() => initialBundle?.cards ?? null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [cardsError, setCardsError] = useState<string | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)
  const [moviesSegment, setMoviesSegment] = useState<'rated' | 'watchlist'>(() => {
    const m = (location.state as { moviesSegment?: string } | null)?.moviesSegment
    return m === 'watchlist' ? 'watchlist' : 'rated'
  })
  const [myWatchlist, setMyWatchlist] = useState<WatchlistFilmPage | null>(null)
  const [watchlistErr, setWatchlistErr] = useState<string | null>(null)
  const [watchlistLoading, setWatchlistLoading] = useState(false)
  const [watchlistLoadingMore, setWatchlistLoadingMore] = useState(false)
  const [exportBusy, setExportBusy] = useState(false)
  const [exportOk, setExportOk] = useState<string | null>(null)
  const [exportTelegramErr, setExportTelegramErr] = useState<{
    message: string
    botUsername: string | null
  } | null>(null)
  const [exportGenericErr, setExportGenericErr] = useState<string | null>(null)
  const [feedPosts, setFeedPosts] = useState<UserFeedPostsPage | null>(null)
  const [postsLoading, setPostsLoading] = useState(false)
  const [postsErr, setPostsErr] = useState<string | null>(null)
  const [postsLoadingMore, setPostsLoadingMore] = useState(false)
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

  useEffect(() => {
    if (auth.kind !== 'ready') {
      return
    }
    let alive = true
    void (async () => {
      try {
        const p = await getMyProfile()
        if (!alive) {
          return
        }
        setProfile(p)
        setLoadError(null)
        setCardsError(null)
      } catch (e) {
        if (!alive) {
          return
        }
        if (e instanceof ApiError) {
          setLoadError(formatApiDetail(e.detail))
        } else {
          setLoadError(e instanceof Error ? e.message : 'Ошибка загрузки')
        }
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind])

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
        const page = await getUserCards(profile.id, {
          limit: 20,
          ...ratedCardsToListParams(deferredRatedQuery),
        })
        if (!alive) {
          return
        }
        setMyCards(page)
        if (isDefaultRatedCardsQuery(ratedQuery)) {
          writeMyProfileBundleCache(profile, page)
        }
      } catch (e) {
        if (!alive) {
          return
        }
        if (e instanceof ApiError) {
          setCardsError(formatApiDetail(e.detail))
        } else {
          setCardsError(e instanceof Error ? e.message : 'Ошибка загрузки')
        }
      } finally {
        if (alive) {
          setRatedCardsLoading(false)
        }
      }
    })()
    return () => {
      alive = false
    }
    // ratedQuery сериализован в ratedQueryKey; не тянем весь profile, чтобы не перезагружать при смене счётчиков.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- profile.id, ratedQuery via key
  }, [auth.kind, profile?.id, mainTab, moviesSegment, ratedQueryKey])

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
        const page = await getUserCards(profile.id, { favoritesOnly: true, limit: 30 })
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

  useEffect(() => {
    if (auth.kind !== 'ready' || profile == null || mainTab !== 'movies' || moviesSegment !== 'watchlist') {
      return
    }
    let alive = true
    void (async () => {
      setWatchlistLoading(true)
      setWatchlistErr(null)
      try {
        const page = await getUserWatchlist(profile.id, { limit: 20 })
        if (!alive) return
        setMyWatchlist(page)
      } catch (e) {
        if (!alive) return
        setWatchlistErr(
          e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить список',
        )
      } finally {
        if (alive) setWatchlistLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind, profile, mainTab, moviesSegment])

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

  const loadMoreCards = useCallback(async () => {
    if (profile == null || myCards?.next_cursor == null || myCards.next_cursor === '') {
      return
    }
    setLoadingMore(true)
    setCardsError(null)
    try {
      const page = await getUserCards(profile.id, {
        cursor: myCards.next_cursor,
        limit: 20,
        ...ratedCardsToListParams(deferredRatedQuery),
      })
      setMyCards((prev) => {
        if (prev == null) {
          if (isDefaultRatedCardsQuery(ratedQuery)) {
            writeMyProfileBundleCache(profile, page)
          }
          return page
        }
        const next: MovieCardPage = {
          items: [...prev.items, ...page.items],
          next_cursor: page.next_cursor,
        }
        if (isDefaultRatedCardsQuery(ratedQuery)) {
          writeMyProfileBundleCache(profile, next)
        }
        return next
      })
    } catch (e) {
      if (e instanceof ApiError) {
        setCardsError(formatApiDetail(e.detail))
      } else {
        setCardsError(e instanceof Error ? e.message : 'Ошибка загрузки')
      }
    } finally {
      setLoadingMore(false)
    }
  }, [profile, myCards, deferredRatedQuery, ratedQuery])

  const loadMoreWatchlist = useCallback(async () => {
    if (profile == null || myWatchlist?.next_cursor == null || myWatchlist.next_cursor === '') {
      return
    }
    setWatchlistLoadingMore(true)
    setWatchlistErr(null)
    try {
      const page = await getUserWatchlist(profile.id, {
        cursor: myWatchlist.next_cursor,
        limit: 20,
      })
      setMyWatchlist((prev) => {
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
        setWatchlistErr(formatApiDetail(e.detail))
      } else {
        setWatchlistErr(e instanceof Error ? e.message : 'Ошибка загрузки')
      }
    } finally {
      setWatchlistLoadingMore(false)
    }
  }, [profile, myWatchlist])

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
    setMyCards((prev) => {
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

  async function runExportCardsCsv() {
    setExportBusy(true)
    setExportOk(null)
    setExportTelegramErr(null)
    setExportGenericErr(null)
    try {
      await postExportMyCardsCsv()
      setExportOk('Файл с карточками отправлен в Telegram — откройте чат с ботом Filmony.')
    } catch (e) {
      if (e instanceof ApiError) {
        if (isTelegramChatUnavailableDetail(e.detail)) {
          setExportTelegramErr({
            message: e.detail.message,
            botUsername: e.detail.bot_username ?? null,
          })
        } else {
          setExportGenericErr(notificationFailureMessage(e.detail))
        }
      } else {
        setExportGenericErr(e instanceof Error ? e.message : 'Не удалось выгрузить')
      }
    } finally {
      setExportBusy(false)
    }
  }

  const ratedCardsLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      auth.kind === 'ready' &&
      mainTab === 'movies' &&
      moviesSegment === 'rated' &&
      Boolean(myCards?.next_cursor) &&
      (myCards?.items.length ?? 0) > 0,
    isBusy: loadingMore,
    onLoadMore: () => void loadMoreCards(),
  })

  const watchlistLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      auth.kind === 'ready' &&
      mainTab === 'movies' &&
      moviesSegment === 'watchlist' &&
      Boolean(myWatchlist?.next_cursor) &&
      (myWatchlist?.items.length ?? 0) > 0,
    isBusy: watchlistLoadingMore,
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
          Откройте приложение в Telegram, чтобы увидеть профиль.
        </p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  if (loadError != null) {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{loadError}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
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

  const pub = toPublicShape(profile)
  const shownName = displayNameFromProfile(pub)
  const canLoadMore = Boolean(myCards?.next_cursor)
  const canLoadMoreWatchlist = Boolean(myWatchlist?.next_cursor)

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-lg font-semibold tracking-tight text-(--tgui--text_color)">Профиль</h1>
          <div className="flex items-center gap-0.5">
            <IconButton
              type="button"
              size="s"
              mode="gray"
              aria-label="Экспорт карточек в CSV в Telegram"
              disabled={exportBusy}
              onClick={() => void runExportCardsCsv()}
            >
              <Download className="relative z-1 block size-[18px]" strokeWidth={1.75} aria-hidden />
            </IconButton>
            <Link
              to="/profile/edit"
              className="flex h-10 w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color) no-underline active:opacity-70"
              aria-label="Настройки профиля"
            >
              ⚙
            </Link>
          </div>
        </div>
      </header>

      <main className="px-4 py-6">
        <div className="flex flex-col items-center text-center">
          <Avatar
            src={profile.photo_url ?? undefined}
            acronym={profileInitials(pub)}
            size={96}
          />
          <Title className="mt-3" level="2" weight="2">
            {shownName}
          </Title>
          <p className="mt-1 font-mono text-[11px] text-(--tgui--hint_color)">@{profile.profile_slug}</p>
          <div className="mt-4 grid w-full max-w-sm grid-cols-2 gap-2">
            <button
              type="button"
              className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center transition-opacity active:opacity-80"
              onClick={() => void navigate('/profile/subscriptions?tab=followers')}
            >
              <span className="block text-lg font-semibold tabular-nums">{shownCount(profile.followers_count)}</span>
              <span className="text-[11px] text-(--tgui--hint_color)">подписчиков</span>
            </button>
            <button
              type="button"
              className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center transition-opacity active:opacity-80"
              onClick={() => void navigate('/profile/subscriptions?tab=following')}
            >
              <span className="block text-lg font-semibold tabular-nums">{shownCount(profile.following_count)}</span>
              <span className="text-[11px] text-(--tgui--hint_color)">подписок</span>
            </button>
            <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center">
              <span className="block text-lg font-semibold tabular-nums">{shownCount(profile.cards_count)}</span>
              <span className="text-[11px] text-(--tgui--hint_color)">оценено</span>
            </div>
            <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center">
              <span className="block text-lg font-semibold tabular-nums">{shownCount(profile.watchlist_count)}</span>
              <span className="text-[11px] text-(--tgui--hint_color)">к просмотру</span>
            </div>
            <div className="col-span-2 rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-2 text-center">
              <span className="block text-lg font-semibold tabular-nums">{shownCount(profile.favorites_count)}</span>
              <span className="text-[11px] text-(--tgui--hint_color)">в любимых</span>
            </div>
          </div>
        </div>

        {profile.bio ? (
          <p className="filmony-text-panel mt-4 text-center text-sm leading-relaxed text-(--tgui--hint_color)">
            {profile.bio}
          </p>
        ) : null}

        {exportOk != null ? (
          <p className="filmony-text-panel mt-4 text-center text-sm text-[color-mix(in_srgb,var(--tgui--hint_color)_92%,var(--tgui--link_color)_8%)]">
            {exportOk}
          </p>
        ) : null}
        {exportTelegramErr != null ? (
          <div className="mx-auto mt-4 max-w-sm rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-4 py-3">
            <p className="text-sm font-medium text-(--tgui--text_color)">Нужен чат с ботом</p>
            <p className="filmony-text-panel mt-1 text-sm leading-relaxed text-(--tgui--hint_color)">
              {exportTelegramErr.message}
            </p>
            {telegramBotOpenUrl(exportTelegramErr.botUsername) != null ? (
              <div className="mt-3">
                <Button
                  size="s"
                  stretched
                  onClick={() => {
                    const u = telegramBotOpenUrl(exportTelegramErr.botUsername)
                    if (u) {
                      openTelegramDeepLink(u)
                    }
                  }}
                >
                  Открыть бота
                </Button>
              </div>
            ) : null}
          </div>
        ) : null}
        {exportGenericErr != null ? (
          <p className="filmony-text-panel mt-4 text-center text-sm text-(--tgui--destructive_text_color)">
            {exportGenericErr}
          </p>
        ) : null}

        <div className="mt-6 grid grid-cols-3 gap-1 rounded-full bg-(--tgui--secondary_bg_color) p-1">
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
          <div className="mt-6">
            <div className="mb-4 flex gap-1 rounded-full bg-(--tgui--secondary_bg_color) p-1">
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
                К просмотру
              </button>
            </div>

            {moviesSegment === 'rated' ? (
              <>
                <FavoriteMoviesStrip items={favoriteStripItems} />
                <ProfileRatedCardsFilters
                  profileUserId={profile.id}
                  cardsQuery={ratedQuery}
                  onChange={setRatedQuery}
                />
                {ratedCardsLoading ? (
                  <p className="filmony-text-panel mb-2 text-center text-xs text-(--tgui--hint_color)">
                    Обновляем список…
                  </p>
                ) : null}
                {cardsError != null ? (
                  <p className="filmony-text-panel mb-2 text-center text-sm text-(--tgui--destructive_text_color)">
                    {cardsError}
                  </p>
                ) : null}
                {myCards != null && myCards.items.length === 0 && !ratedCardsLoading ? (
                  <div className="filmony-text-panel py-8 text-center">
                    <p className="text-sm text-(--tgui--hint_color)">
                      {isDefaultRatedCardsQuery(ratedQuery)
                        ? 'Ещё нет оценённых карточек'
                        : 'Нет карточек с такими фильтрами'}
                    </p>
                  </div>
                ) : null}
                {myCards != null && myCards.items.length > 0 ? (
                  <div className="px-1">
                    <MoviePosterGrid
                      items={myCards.items}
                      showFavoriteToggle
                      onFavoriteToggled={handleFavoriteToggled}
                    />
                  </div>
                ) : null}
                {canLoadMore ? (
                  <>
                    <div ref={ratedCardsLoadMoreRef} className="mt-2 h-1 w-full shrink-0" aria-hidden />
                    {loadingMore ? (
                      <p className="mt-2 text-center text-xs text-(--tgui--hint_color)">Подгружаем карточки…</p>
                    ) : null}
                  </>
                ) : null}
              </>
            ) : (
              <>
                {watchlistErr != null ? (
                  <p className="filmony-text-panel mb-2 text-center text-sm text-(--tgui--destructive_text_color)">
                    {watchlistErr}
                  </p>
                ) : null}
                {watchlistLoading ? (
                  <p className="filmony-text-panel py-8 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
                ) : null}
                {!watchlistLoading && myWatchlist != null && myWatchlist.items.length === 0 ? (
                  <div className="filmony-text-panel flex flex-col items-center gap-4 py-8 text-center">
                    <p className="text-sm text-(--tgui--hint_color)">В «К просмотру» пока пусто</p>
                    <Link to="/cards/new" className="w-full max-w-xs no-underline">
                      <Button stretched>Добавить в список</Button>
                    </Link>
                  </div>
                ) : null}
                {!watchlistLoading && myWatchlist != null && myWatchlist.items.length > 0 ? (
                  <div className="px-1">
                    <WatchlistPosterGrid items={myWatchlist.items} />
                  </div>
                ) : null}
                {canLoadMoreWatchlist ? (
                  <>
                    <div ref={watchlistLoadMoreRef} className="mt-2 h-1 w-full shrink-0" aria-hidden />
                    {watchlistLoadingMore ? (
                      <p className="mt-2 text-center text-xs text-(--tgui--hint_color)">Подгружаем список…</p>
                    ) : null}
                  </>
                ) : null}
              </>
            )}
          </div>
        ) : null}

        {mainTab === 'posts' ? (
          <div className="mt-6 space-y-3">
            {postsErr != null ? (
              <p className="filmony-text-panel text-center text-sm text-(--tgui--destructive_text_color)">{postsErr}</p>
            ) : null}
            {postsLoading ? (
              <p className="filmony-text-panel py-8 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
            ) : null}
            {!postsLoading && feedPosts != null && feedPosts.items.length === 0 ? (
              <div className="filmony-text-panel py-8 text-center">
                <p className="text-sm text-(--tgui--hint_color)">Пока нет постов в ленте</p>
              </div>
            ) : null}
            {!postsLoading && feedPosts != null && feedPosts.items.length > 0 ? (
              <div className="flex flex-col gap-3 px-1">
                {feedPosts.items.map((post) => (
                  <FeedPostCard key={`profile-post-${post.id}`} post={post} viewerUserId={profile.id} />
                ))}
                {feedPosts.next_cursor != null && feedPosts.next_cursor !== '' ? (
                  <>
                    <div ref={postsLoadMoreRef} className="h-1 w-full shrink-0" aria-hidden />
                    {postsLoadingMore ? (
                      <p className="text-center text-xs text-(--tgui--hint_color)">Подгружаем посты…</p>
                    ) : null}
                  </>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}

        {mainTab === 'stats' ? (
          <div className="mt-6">
            <ProfileStatsPanel userId={profile.id} />
          </div>
        ) : null}
      </main>

    </div>
  )
}
