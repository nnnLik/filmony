import { Button } from '@telegram-apps/telegram-ui'
import { useQuery, useQueryClient, type InfiniteData } from '@tanstack/react-query'
import { useCallback, useDeferredValue, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router'

import { ApiError, formatApiDetail } from '../api/client'
import {
  getPublicProfileById,
  getUserSubscriptions,
  subscribeToUser,
  unsubscribeFromUser,
} from '../api/profileApi'
import type { MovieCardPage, PublicProfile } from '../api/profileTypes'
import {
  ratedCardsQueryKey,
} from '../lib/ratedCardsListQuery'
import { useAuthStatus } from '../auth/useAuthStatus'
import { useTasteQuizKnowledgeOfUsers } from '../hooks/useTasteQuizKnowledgeOfUsers'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { useRatedCardsQueryFromUrl } from '../hooks/useRatedCardsQueryFromUrl'
import { useMyProfileQuery } from '../hooks/useMyProfileQuery'
import { useProfileMoviesContent } from '../hooks/useProfileMoviesContent'
import { ProfileCompactMetrics } from '../components/profile/ProfileCompactMetrics'
import { ProfileIdentityCard } from '../components/profile/ProfileIdentityCard'
import { type ProfileMainTab } from '../components/profile/profileMainTab'
import {
  ProfileSectionTabs,
  profileSectionOf,
  type ProfileSection,
} from '../components/profile/ProfileSectionTabs'
import { ProfileRatedPanel } from '../components/profile/ProfileRatedPanel'
import { ProfileStatsTab } from '../components/profile/ProfileStatsTab'
import { ProfileWatchlistPanel } from '../components/profile/ProfileWatchlistPanel'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import type { ProfileMoviesSegment } from '../lib/profileMoviesSegment'
import {
  userCardsQueryKey,
  userFollowingStatusQueryKey,
  userPublicProfileQueryKey,
} from '../lib/profileQueryKeys'

export function PublicProfilePage() {
  const { userId } = useParams<{ userId?: string }>()
  const resolvedUserId = useMemo(() => decodeURIComponent(userId ?? ''), [userId])
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()

  const [mainTab, setMainTab] = useState<ProfileMainTab>('movies')
  const [moviesSegment, setMoviesSegment] = useState<ProfileMoviesSegment>('rated')
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
    eagerWatchlist: true,
  })

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

  const handleSectionChange = useCallback((section: ProfileSection) => {
    if (section === 'stats') {
      setMainTab('stats')
      return
    }
    setMainTab('movies')
    setMoviesSegment(section)
  }, [])

  const handleNavigateBack = useCallback(() => {
    const st = location.state as { cardEntry?: string } | undefined
    if (st?.cardEntry === 'telegram_start_param' || location.key === 'default') {
      void navigate('/')
      return
    }
    void navigate(-1)
  }, [location.key, location.state, navigate])

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
    return <PageLoadingState authPending />
  }

  if (auth.kind === 'error') {
    return <PageErrorState message={auth.message} backLabel="На главную" backHref="/" />
  }

  if (auth.kind === 'skipped') {
    return (
      <PageErrorState
        message="Войдите через Telegram Mini App, чтобы открыть профиль."
        backLabel="На главную"
        backHref="/"
      />
    )
  }

  if (resolvedUserId === '') {
    return <PageErrorState message="Не указан пользователь." backLabel="К профилю" backHref="/profile" />
  }

  if (error != null) {
    return <PageErrorState message={error} backLabel="К профилю" backHref="/profile" />
  }

  if (profile == null) {
    return <PageLoadingState />
  }

  const isOwnPublicProfile = myUserId != null && myUserId === profile.id
  const canFollow = myUserId != null && profile.id !== myUserId

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) pb-6 text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <button
          type="button"
          onClick={handleNavigateBack}
          className="flex min-h-10 min-w-10 items-center justify-center rounded-lg text-lg text-(--tgui--link_color)"
          aria-label="Назад"
        >
          ←
        </button>
        <span className="truncate text-sm font-medium text-(--tgui--hint_color)">Профиль</span>
      </header>

      <div className="mx-auto max-w-md px-4 pt-4">
        <ProfileIdentityCard
          profile={profile}
          viewerId={myUserId}
          knowledgeByOwnerId={knowledgeByOwnerId}
          streakByUserId={streakByUserId}
          headerAction={
            canFollow ? (
              <Button
                size="s"
                mode={isFollowing ? 'bezeled' : 'filled'}
                disabled={followBusy}
                onClick={() => void toggleFollowing()}
              >
                {followBusy ? '...' : isFollowing ? 'Отписаться' : 'Подписаться'}
              </Button>
            ) : null
          }
          metrics={
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
          }
          actions={
            canFollow && isFollowing ? (
              <Button
                size="s"
                mode="bezeled"
                stretched
                onClick={() => void navigate(`/taste-quiz/play/${encodeURIComponent(profile.id)}`)}
              >
                Угадать вкус
              </Button>
            ) : null
          }
        />

        {followError != null ? (
          <p className="mt-3 text-center text-sm text-(--tgui--destructive_text_color)">
            {followError}
          </p>
        ) : null}

        <ProfileSectionTabs
          value={profileSectionOf(mainTab, moviesSegment)}
          onChange={handleSectionChange}
          counts={{
            rated: profile.cards_count,
            watchlist: profile.watchlist_count,
          }}
          sticky
          className="mt-5"
        />

        {mainTab === 'movies' ? (
          <div className="mt-4" id="profile-rated-cards-panel">
            {moviesSegment === 'rated' ? (
              <ProfileRatedPanel
                profileUserId={profile.id}
                viewerUserId={myUserId}
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
                emptyUserId={myUserId}
                emptyFallback="Пока нет карточек."
                filteredEmptyFallback="Нет карточек с такими фильтрами."
                showFavoriteToggle={isOwnPublicProfile}
                onFavoriteToggled={isOwnPublicProfile ? handleFavoriteToggled : undefined}
              />
            ) : (
              <ProfileWatchlistPanel
                watchlist={watchlist}
                error={watchlistError}
                canLoadMore={canLoadMoreWatchlist}
                isFetchingNextPage={watchlistQuery.isFetchingNextPage}
                loadMoreRef={watchlistLoadMoreRef}
              />
            )}
          </div>
        ) : (
          <ProfileStatsTab
            className="mt-4"
            userId={profile.id}
            cardsQuery={ratedQuery}
            onCardsQueryChange={setRatedQuery}
            enableCategoryFilter
            showPassportCollection
            onDrillToRatedCards={drillToRatedCards}
          />
        )}
      </div>
    </div>
  )
}
