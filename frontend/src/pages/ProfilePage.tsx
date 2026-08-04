import { Avatar, Button, IconButton, Title } from '@telegram-apps/telegram-ui'
import { useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { Download, Settings } from 'lucide-react'
import { lazy, Suspense, useCallback, useDeferredValue, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import { ApiError, formatApiDetail } from '../api/client'
import { postExportMyCardsCsv } from '../api/profileApi'
import type {
  MovieCardPage,
  MyProfile,
  PublicProfile,
} from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { FavoriteMoviesStrip } from '../components/profile/FavoriteMoviesStrip'
import { MoviePosterGrid } from '../components/profile/MoviePosterGrid'
import { ProfileCompactMetrics } from '../components/profile/ProfileCompactMetrics'
import { ProfileRatedCardsFilters } from '../components/profile/ProfileRatedCardsFilters'
import { ProfileShelfPhysics } from '../components/profile/gamification/ProfileShelfPhysics'
import { MarathonShelfFrame } from '../components/profile/gamification/MarathonShelfFrame'
import { WatchlistPosterGrid } from '../components/profile/WatchlistPosterGrid'
import { WatchlistOverlapSection } from '../components/watchlist/WatchlistOverlapSection'
import { FeedPostCard } from '../components/feed/FeedPostCard'
import { PageHeader } from '../components/layout/PageHeader'
import { PlayfulHint } from '../components/ui/PlayfulHint'
import { InlineLoadingState } from '../components/ui/InlineLoadingState'
import { SegmentedControl } from '../components/ui/SegmentedControl'
import { RatingStreakAuthorBadge } from '../components/streaks/RatingStreakAuthorBadge'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { useMyProfileQuery } from '../hooks/useMyProfileQuery'
import { useUserCardsInfiniteQuery } from '../hooks/useUserCardsInfiniteQuery'
import { useUserWatchlistInfiniteQuery } from '../hooks/useUserWatchlistInfiniteQuery'
import { useUserFeedPostsInfiniteQuery } from '../hooks/useUserFeedPostsInfiniteQuery'
import { useUserFavoritesStripQuery } from '../hooks/useUserFavoritesStripQuery'
import { useMyLatestMonthlyRecapQuery } from '../hooks/useMyLatestMonthlyRecapQuery'
import { readMyProfileBundleCache, writeMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { marathonDrillToRatedQuery } from '../lib/marathonDrillToRatedQuery'
import {
  isDefaultRatedCardsQuery,
  ratedCardsQueryKey,
} from '../lib/ratedCardsListQuery'
import { displayNameFromProfile, profileInitials } from '../lib/profileDisplay'
import {
  isTelegramChatUnavailableDetail,
  notificationFailureMessage,
  openTelegramDeepLink,
  telegramBotOpenUrl,
} from '../lib/telegramNotificationError'
import { useInfiniteScrollLoadMore } from '../hooks/useInfiniteScrollLoadMore'
import { useGamification } from '../hooks/useGamification'
import { useProfileMoviesSegmentFromUrl } from '../hooks/useProfileMoviesSegmentFromUrl'
import { useRatedCardsQueryFromUrl } from '../hooks/useRatedCardsQueryFromUrl'
import { computeShelfPhysicsFromCards } from '../lib/gamification/shelfPhysicsFallback'
import type { MarathonAchievement } from '../api/gamificationTypes'
import { myProfileQueryKey, userCardsQueryKey } from '../lib/profileQueryKeys'
import { scheduleDeferredPepeDancingPrewarm } from '../lib/pepeGif'
import './ProfilePage.css'

const ProfileStatsPanel = lazy(() =>
  import('../components/profile/ProfileStatsPanel').then((m) => ({ default: m.ProfileStatsPanel })),
)

type ProfileMainTab = 'movies' | 'posts' | 'stats'

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
  const queryClient = useQueryClient()
  const initialBundle = useMemo(() => readMyProfileBundleCache(), [])

  const [mainTab, setMainTab] = useState<ProfileMainTab>('movies')
  const [moviesSegment, setMoviesSegment] = useProfileMoviesSegmentFromUrl()
  const [exportBusy, setExportBusy] = useState(false)
  const [exportOk, setExportOk] = useState<string | null>(null)
  const [exportTelegramErr, setExportTelegramErr] = useState<{
    message: string
    botUsername: string | null
  } | null>(null)
  const [exportGenericErr, setExportGenericErr] = useState<string | null>(null)
  const [recapDismissedKey, setRecapDismissedKey] = useState<string | null>(null)
  const [ratedQuery, setRatedQuery] = useRatedCardsQueryFromUrl()
  const deferredRatedQuery = useDeferredValue(ratedQuery)
  const ratedQueryKey = useMemo(
    () => ratedCardsQueryKey(deferredRatedQuery),
    [deferredRatedQuery],
  )

  const profileQuery = useMyProfileQuery()
  const profile = profileQuery.data ?? null
  const loadError =
    profileQuery.error instanceof ApiError
      ? formatApiDetail(profileQuery.error.detail)
      : profileQuery.error != null
        ? profileQuery.error.message
        : null

  const cardsEnabled =
    auth.kind === 'ready' &&
    profile != null &&
    mainTab === 'movies' &&
    moviesSegment === 'rated'

  const cardsQuery = useUserCardsInfiniteQuery(profile?.id ?? '', ratedQuery, {
    enabled: cardsEnabled,
    initialPage:
      isDefaultRatedCardsQuery(ratedQuery) && initialBundle?.cards != null
        ? initialBundle.cards
        : undefined,
    initialPageUpdatedAt: initialBundle?.storedAt,
  })

  const myCards = useMemo(() => {
    const pages = cardsQuery.data?.pages
    if (pages == null || pages.length === 0) {
      return null
    }
    return {
      items: pages.flatMap((p) => p.items),
      next_cursor: pages[pages.length - 1]?.next_cursor ?? null,
    }
  }, [cardsQuery.data])

  const watchlistQuery = useUserWatchlistInfiniteQuery(profile?.id ?? '', {
    enabled:
      auth.kind === 'ready' &&
      profile != null &&
      mainTab === 'movies' &&
      moviesSegment === 'watchlist',
  })

  const myWatchlist = useMemo(() => {
    const pages = watchlistQuery.data?.pages
    if (pages == null || pages.length === 0) {
      return null
    }
    return {
      items: pages.flatMap((p) => p.items),
      next_cursor: pages[pages.length - 1]?.next_cursor ?? null,
    }
  }, [watchlistQuery.data])

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

  const recapQuery = useMyLatestMonthlyRecapQuery()
  const recapBanner = useMemo(() => {
    const recap = recapQuery.data
    if (recap == null || recap.total_rated <= 0) {
      return null
    }
    const key = `recap_dismissed_${recap.year}_${recap.month}`
    if (localStorage.getItem(key) === '1' || recapDismissedKey === key) {
      return null
    }
    return recap
  }, [recapQuery.data, recapDismissedKey])

  const streakUserIds = useMemo(() => {
    if (profile == null) return []
    return [profile.id]
  }, [profile])
  const { streakByUserId } = useRatingStreaksOfUsers(streakUserIds, {
    enabled: streakUserIds.length > 0,
  })

  const gamificationQuery = useGamification({
    enabled:
      auth.kind === 'ready' &&
      profile != null &&
      mainTab === 'movies' &&
      moviesSegment === 'rated' &&
      (myCards?.items.length ?? 0) > 0,
  })

  const shelfPhysicsMode = useMemo(() => {
    if (gamificationQuery.data?.shelf_physics.mode != null) {
      return gamificationQuery.data.shelf_physics.mode
    }
    const items = myCards?.items
    if (items != null && items.length > 0 && isDefaultRatedCardsQuery(ratedQuery)) {
      return computeShelfPhysicsFromCards(items).mode
    }
    return 'neutral' as const
  }, [gamificationQuery.data, myCards, ratedQuery])

  const unlockedMarathons = gamificationQuery.data?.marathons ?? []

  useEffect(() => {
    scheduleDeferredPepeDancingPrewarm()
  }, [])

  useEffect(() => {
    if (profile == null || cardsQuery.data == null || !isDefaultRatedCardsQuery(ratedQuery)) {
      return
    }
    writeMyProfileBundleCache(profile, myCards)
  }, [profile, cardsQuery.data, ratedQuery, myCards])

  const cardsError =
    cardsQuery.error instanceof ApiError
      ? formatApiDetail(cardsQuery.error.detail)
      : cardsQuery.error != null
        ? cardsQuery.error.message
        : null

  const ratedCardsLoading = cardsQuery.isFetching && !cardsQuery.isFetchingNextPage

  const watchlistErr =
    watchlistQuery.error instanceof ApiError
      ? formatApiDetail(watchlistQuery.error.detail)
      : watchlistQuery.error != null
        ? 'Не удалось загрузить список'
        : null

  const watchlistLoading = watchlistQuery.isPending && watchlistQuery.fetchStatus === 'fetching'

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
      queryClient.setQueryData<MyProfile>(myProfileQueryKey(), (prev) => {
        if (prev == null) {
          return prev
        }
        return {
          ...prev,
          favorites_count: Math.max(0, prev.favorites_count + (nextFavorite ? 1 : -1)),
        }
      })
    },
    [profile, queryClient, ratedQueryKey],
  )

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

  const drillToRatedCards = useCallback(() => {
    setMainTab('movies')
    setMoviesSegment('rated')
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        document.getElementById('profile-rated-cards-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    })
  }, [setMoviesSegment])

  const handleMarathonDrill = useCallback(
    (marathon: MarathonAchievement) => {
      if (marathon.kind === 'director') {
        const parsed = Number.parseInt(marathon.key, 10)
        const id =
          Number.isInteger(parsed) && parsed >= 1 ? String(parsed) : marathon.key.trim()
        if (id !== '') {
          void navigate(`/directors/${encodeURIComponent(id)}`)
        }
        return
      }
      if (marathon.kind === 'franchise') {
        const key = marathon.key.trim()
        if (key !== '') {
          void navigate(`/franchises/${encodeURIComponent(key)}`)
        }
        return
      }
      setRatedQuery((prev) => marathonDrillToRatedQuery(prev, marathon))
      drillToRatedCards()
    },
    [drillToRatedCards, navigate, setRatedQuery],
  )

  const drillToWatchlist = useCallback(() => {
    setMainTab('movies')
    setMoviesSegment('watchlist')
  }, [setMoviesSegment])

  const drillToRatedSegment = useCallback(() => {
    setMainTab('movies')
    setMoviesSegment('rated')
  }, [setMoviesSegment])

  const ratedCardsLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      cardsEnabled &&
      Boolean(myCards?.next_cursor) &&
      (myCards?.items.length ?? 0) > 0,
    isBusy: cardsQuery.isFetchingNextPage,
    onLoadMore: () => void cardsQuery.fetchNextPage(),
  })

  const watchlistLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      auth.kind === 'ready' &&
      mainTab === 'movies' &&
      moviesSegment === 'watchlist' &&
      Boolean(myWatchlist?.next_cursor) &&
      (myWatchlist?.items.length ?? 0) > 0,
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

  if (auth.kind === 'loading') {
    return <InlineLoadingState message="Вход…" />
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
    return <InlineLoadingState message="Загрузка…" />
  }

  const pub = toPublicShape(profile)
  const shownName = displayNameFromProfile(pub)
  const canLoadMore = Boolean(myCards?.next_cursor)
  const canLoadMoreWatchlist = Boolean(myWatchlist?.next_cursor)

  return (
    <div className="min-h-full">
      <PageHeader
        title="Профиль"
        pepeClassName="profile-page__title-pepe"
        actions={
          <>
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
            <Link to="/profile/edit" className="no-underline" aria-label="Настройки профиля">
              <IconButton type="button" size="s" mode="gray" aria-label="Настройки профиля">
                <Settings className="relative z-1 block size-[18px]" strokeWidth={1.75} aria-hidden />
              </IconButton>
            </Link>
          </>
        }
      />

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
          {profile != null ? (
            <div className="mt-1 flex justify-center">
              <RatingStreakAuthorBadge streakByUserId={streakByUserId} authorId={profile.id} />
            </div>
          ) : null}
          <p className="mt-1 font-mono text-[11px] text-(--tgui--hint_color)">@{profile.profile_slug}</p>
          <div className="mt-4 w-full max-w-sm">
            <ProfileCompactMetrics
              followers_count={profile.followers_count}
              following_count={profile.following_count}
              cards_count={profile.cards_count}
              watchlist_count={profile.watchlist_count}
              favorites_count={profile.favorites_count}
              onFollowersClick={() => void navigate('/profile/subscriptions?tab=followers')}
              onFollowingClick={() => void navigate('/profile/subscriptions?tab=following')}
              onRatedClick={drillToRatedSegment}
              onWatchlistClick={drillToWatchlist}
              onFavoritesClick={drillToRatedSegment}
            />
          </div>
        </div>

        {profile.bio ? (
          <p className="filmony-text-panel mt-4 text-center text-sm leading-relaxed text-(--tgui--hint_color)">
            {profile.bio}
          </p>
        ) : null}

        {recapBanner != null ? (
          <div className="mx-auto mt-4 max-w-sm rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-4 py-3 text-left">
            <p className="text-sm font-medium text-(--tgui--text_color)">Итоги месяца готовы</p>
            <p className="filmony-text-panel mt-1 text-sm text-(--tgui--hint_color)">
              {recapBanner.total_rated} оценок за последний полный месяц — открой сводку.
            </p>
            <div className="mt-3 flex gap-2">
              <Button
                size="s"
                stretched
                onClick={() => {
                  void navigate(`/me/recap/${recapBanner.year}/${recapBanner.month}`)
                }}
              >
                Посмотреть
              </Button>
              <Button
                size="s"
                mode="gray"
                onClick={() => {
                  const key = `recap_dismissed_${recapBanner.year}_${recapBanner.month}`
                  localStorage.setItem(key, '1')
                  setRecapDismissedKey(key)
                }}
              >
                Скрыть
              </Button>
            </div>
          </div>
        ) : null}

        <div className="mt-4 flex justify-center">
          <Button mode="gray" onClick={() => void navigate('/taste-quiz/invite')}>
            Пригласить угадать
          </Button>
        </div>

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

        <div className="mt-6">
          <SegmentedControl
            value={mainTab}
            onChange={setMainTab}
            ariaLabel="Раздел профиля"
            layout="grid"
            gridColsClassName="grid-cols-3"
            segments={[
              { value: 'movies', label: 'Карточки' },
              { value: 'posts', label: 'Посты' },
              { value: 'stats', label: 'Статистика' },
            ]}
          />
        </div>

        {mainTab === 'movies' ? (
          <div className="mt-6" id="profile-rated-cards-panel">
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
                Позже
              </button>
            </div>

            {moviesSegment === 'rated' ? (
              <>
                <FavoriteMoviesStrip items={favoriteStripItems} />
                <ProfileRatedCardsFilters
                  profileUserId={profile.id}
                  viewerUserId={profile.id}
                  cardsQuery={ratedQuery}
                  onChange={setRatedQuery}
                  enableCategoryFilter
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
                    <MarathonShelfFrame marathons={unlockedMarathons} onMarathonDrill={handleMarathonDrill}>
                      <ProfileShelfPhysics mode={shelfPhysicsMode}>
                        <MoviePosterGrid
                          items={myCards.items}
                          showFavoriteToggle
                          showContrarianBadge
                          onFavoriteToggled={handleFavoriteToggled}
                        />
                      </ProfileShelfPhysics>
                    </MarathonShelfFrame>
                  </div>
                ) : null}
                {canLoadMore ? (
                  <>
                    <div ref={ratedCardsLoadMoreRef} className="mt-2 h-1 w-full shrink-0" aria-hidden />
                    {cardsQuery.isFetchingNextPage ? (
                      <p className="mt-2 text-center text-xs text-(--tgui--hint_color)">Подгружаем карточки…</p>
                    ) : null}
                  </>
                ) : null}
              </>
            ) : (
              <>
                <WatchlistOverlapSection enabled={!watchlistLoading} />
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
                    <p className="text-sm text-(--tgui--hint_color)">В списке «Позже» пока пусто</p>
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
                    {watchlistQuery.isFetchingNextPage ? (
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
                <PlayfulHint
                  poolKey="profile_posts_empty"
                  fallback="Пока нет постов в ленте"
                  userId={profile.id}
                  className="text-sm text-(--tgui--hint_color)"
                />
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
                    {postsQuery.isFetchingNextPage ? (
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
            <Suspense fallback={<InlineLoadingState message="Загрузка статистики…" />}>
              <ProfileStatsPanel
                userId={profile.id}
                cardsQuery={ratedQuery}
                onCardsQueryChange={setRatedQuery}
                enableCategoryFilter
                showTasteQuizTeaser
                showPassportCollection
                onMarathonDrill={handleMarathonDrill}
                onDrillToRatedCards={drillToRatedCards}
              />
            </Suspense>
          </div>
        ) : null}
      </main>

    </div>
  )
}
