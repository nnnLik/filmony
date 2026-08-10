import { Button, IconButton } from '@telegram-apps/telegram-ui'
import { useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { Download, Settings } from 'lucide-react'
import { useCallback, useDeferredValue, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import { ApiError, formatApiDetail } from '../api/client'
import { postExportMyCardsCsv } from '../api/profileApi'
import type {
  MovieCardPage,
  MyProfile,
  PublicProfile,
} from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { ProfileHeader } from '../components/profile/ProfileHeader'
import { ProfileMainTabs, type ProfileMainTab } from '../components/profile/ProfileMainTabs'
import { ProfileMoviesSegmentToggle } from '../components/profile/ProfileMoviesSegmentToggle'
import { ProfileRatedPanel } from '../components/profile/ProfileRatedPanel'
import { ProfileCollectionsPanel } from '../components/profile/ProfileCollectionsPanel'
import { ProfileStatsTab } from '../components/profile/ProfileStatsTab'
import { ProfileWatchlistPanel } from '../components/profile/ProfileWatchlistPanel'
import { PageHeader } from '../components/layout/PageHeader'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { useWatchingNowOfUsers } from '../hooks/useWatchingNowOfUsers'
import { useMyProfileQuery } from '../hooks/useMyProfileQuery'
import { useMyLatestMonthlyRecapQuery } from '../hooks/useMyLatestMonthlyRecapQuery'
import { useProfileMoviesContent } from '../hooks/useProfileMoviesContent'
import { readMyProfileBundleCache, writeMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { marathonDrillToRatedQuery } from '../lib/marathonDrillToRatedQuery'
import {
  isDefaultRatedCardsQuery,
  ratedCardsQueryKey,
} from '../lib/ratedCardsListQuery'
import {
  isTelegramChatUnavailableDetail,
  notificationFailureMessage,
  openTelegramDeepLink,
  telegramBotOpenUrl,
} from '../lib/telegramNotificationError'
import { useGamification } from '../hooks/useGamification'
import { useProfileMoviesSegmentFromUrl } from '../hooks/useProfileMoviesSegmentFromUrl'
import { useRatedCardsQueryFromUrl } from '../hooks/useRatedCardsQueryFromUrl'
import { computeShelfPhysicsFromCards } from '../lib/gamification/shelfPhysicsFallback'
import type { MarathonAchievement } from '../api/gamificationTypes'
import { myProfileQueryKey, userCardsQueryKey } from '../lib/profileQueryKeys'
import { scheduleDeferredPepeDancingPrewarm } from '../lib/pepeGif'
import './ProfilePage.css'

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
    pinned_achievements: [],
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

  const authReady = auth.kind === 'ready'

  const {
    cardsQuery,
    watchlistQuery,
    cards,
    watchlist,
    favoriteStripItems,
    cardsError,
    ratedCardsLoading,
    watchlistError,
    watchlistLoading,
    canLoadMoreCards,
    canLoadMoreWatchlist,
    ratedCardsLoadMoreRef,
    watchlistLoadMoreRef,
  } = useProfileMoviesContent({
    profileUserId: profile?.id ?? '',
    authReady,
    mainTab,
    moviesSegment,
    ratedQuery,
    favoritesCount: profile?.favorites_count ?? 0,
    initialCardsPage:
      isDefaultRatedCardsQuery(ratedQuery) && initialBundle?.cards != null
        ? initialBundle.cards
        : undefined,
    initialCardsPageUpdatedAt: initialBundle?.storedAt,
  })

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
  const { watchingByUserId } = useWatchingNowOfUsers(streakUserIds, {
    enabled: streakUserIds.length > 0,
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

  const gamificationQuery = useGamification({
    enabled:
      authReady &&
      profile != null &&
      mainTab === 'movies' &&
      moviesSegment === 'rated' &&
      (cards?.items.length ?? 0) > 0,
  })

  const shelfPhysicsMode = useMemo(() => {
    if (gamificationQuery.data?.shelf_physics.mode != null) {
      return gamificationQuery.data.shelf_physics.mode
    }
    const items = cards?.items
    if (items != null && items.length > 0 && isDefaultRatedCardsQuery(ratedQuery)) {
      return computeShelfPhysicsFromCards(items).mode
    }
    return 'neutral' as const
  }, [gamificationQuery.data, cards, ratedQuery])

  useEffect(() => {
    scheduleDeferredPepeDancingPrewarm()
  }, [])

  useEffect(() => {
    if (profile == null || cardsQuery.data == null || !isDefaultRatedCardsQuery(ratedQuery)) {
      return
    }
    writeMyProfileBundleCache(profile, cards)
  }, [profile, cardsQuery.data, ratedQuery, cards])

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

  if (auth.kind === 'loading') {
    return <PageLoadingState authPending />
  }

  if (auth.kind === 'error') {
    return <PageErrorState message={auth.message} backLabel="На главную" backHref="/" />
  }

  if (loadError != null) {
    return <PageErrorState message={loadError} backLabel="На главную" backHref="/" />
  }

  if (profile == null) {
    return <PageLoadingState />
  }

  const pub = toPublicShape(profile)

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
        <ProfileHeader
          profile={pub}
          showTasteQuizBadge={false}
          streakByUserId={streakByUserId}
          watchingByUserId={watchingByUserId}
          metrics={{
            followers_count: profile.followers_count,
            following_count: profile.following_count,
            cards_count: profile.cards_count,
            watchlist_count: profile.watchlist_count,
            favorites_count: profile.favorites_count,
            onFollowersClick: () => void navigate('/profile/subscriptions?tab=followers'),
            onFollowingClick: () => void navigate('/profile/subscriptions?tab=following'),
            onRatedClick: drillToRatedSegment,
            onWatchlistClick: drillToWatchlist,
            onFavoritesClick: drillToRatedSegment,
          }}
          className="mb-3"
        />

        {profile.bio ? (
          <p className="filmony-text-panel mt-3 text-left text-sm leading-relaxed text-(--tgui--hint_color)">
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

        <div className="mt-4">
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

        <ProfileMainTabs value={mainTab} onChange={setMainTab} className="mt-6" />

        {mainTab === 'movies' ? (
          <div className="mt-6" id="profile-rated-cards-panel">
            <ProfileMoviesSegmentToggle
              value={moviesSegment}
              onChange={setMoviesSegment}
              className="mb-4"
            />

            {moviesSegment === 'rated' ? (
              <ProfileRatedPanel
                profileUserId={profile.id}
                viewerUserId={profile.id}
                ratedQuery={ratedQuery}
                onRatedQueryChange={setRatedQuery}
                enableCategoryFilter
                favoriteStripItems={favoriteStripItems}
                cards={cards}
                loading={ratedCardsLoading}
                error={cardsError}
                canLoadMore={canLoadMoreCards}
                isFetchingNextPage={cardsQuery.isFetchingNextPage}
                loadMoreRef={ratedCardsLoadMoreRef}
                emptyUserId={profile.id}
                showFavoriteToggle
                showContrarianBadge
                onFavoriteToggled={handleFavoriteToggled}
                shelfPhysicsMode={shelfPhysicsMode}
              />
            ) : (
              <ProfileWatchlistPanel
                watchlist={watchlist}
                error={watchlistError}
                loading={watchlistLoading}
                canLoadMore={canLoadMoreWatchlist}
                isFetchingNextPage={watchlistQuery.isFetchingNextPage}
                loadMoreRef={watchlistLoadMoreRef}
                showOverlapSection
                showAddWhenEmpty
              />
            )}
          </div>
        ) : null}

        {mainTab === 'stats' ? (
          <ProfileStatsTab
            className="mt-6"
            userId={profile.id}
            cardsQuery={ratedQuery}
            onCardsQueryChange={setRatedQuery}
            enableCategoryFilter
            showTasteQuizTeaser
            showPassportCollection
            showAchievements
            onMarathonDrill={handleMarathonDrill}
            onDrillToRatedCards={drillToRatedCards}
          />
        ) : null}

        {mainTab === 'collections' ? (
          <ProfileCollectionsPanel userId={profile.id} isOwnProfile className="mt-6" />
        ) : null}
      </main>

    </div>
  )
}
