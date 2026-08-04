import { useMemo } from 'react'

import { ApiError, formatApiDetail } from '../api/client'
import type { MovieCardPage } from '../api/profileTypes'
import type { ProfileMainTab } from '../components/profile/ProfileMainTabs'
import {
  isDefaultRatedCardsQuery,
  type RatedCardsListQuery,
} from '../lib/ratedCardsListQuery'
import type { ProfileMoviesSegment } from '../lib/profileMoviesSegment'
import { useInfiniteScrollLoadMore } from './useInfiniteScrollLoadMore'
import { useUserCardsInfiniteQuery } from './useUserCardsInfiniteQuery'
import { useUserFavoritesStripQuery } from './useUserFavoritesStripQuery'
import { useUserWatchlistInfiniteQuery } from './useUserWatchlistInfiniteQuery'

export type UseProfileMoviesContentOptions = {
  profileUserId: string
  authReady: boolean
  mainTab: ProfileMainTab
  moviesSegment: ProfileMoviesSegment
  ratedQuery: RatedCardsListQuery
  favoritesCount: number
  initialCardsPage?: MovieCardPage | null
  initialCardsPageUpdatedAt?: number
  /** Public profiles load watchlist eagerly on profile open. */
  eagerWatchlist?: boolean
}

export function useProfileMoviesContent(options: UseProfileMoviesContentOptions) {
  const {
    profileUserId,
    authReady,
    mainTab,
    moviesSegment,
    ratedQuery,
    favoritesCount,
    initialCardsPage,
    initialCardsPageUpdatedAt,
    eagerWatchlist = false,
  } = options

  const cardsEnabled =
    authReady &&
    profileUserId !== '' &&
    mainTab === 'movies' &&
    moviesSegment === 'rated'

  const cardsQuery = useUserCardsInfiniteQuery(profileUserId, ratedQuery, {
    enabled: cardsEnabled,
    initialPage:
      isDefaultRatedCardsQuery(ratedQuery) && initialCardsPage != null
        ? initialCardsPage
        : undefined,
    initialPageUpdatedAt: initialCardsPageUpdatedAt,
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

  const watchlistEnabled = eagerWatchlist
    ? authReady && profileUserId !== ''
    : authReady &&
      profileUserId !== '' &&
      mainTab === 'movies' &&
      moviesSegment === 'watchlist'

  const watchlistQuery = useUserWatchlistInfiniteQuery(profileUserId, {
    enabled: watchlistEnabled,
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

  const favoritesStripQuery = useUserFavoritesStripQuery(profileUserId, {
    enabled:
      profileUserId !== '' &&
      favoritesCount > 0 &&
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

  const watchlistError =
    watchlistQuery.error instanceof ApiError
      ? formatApiDetail(watchlistQuery.error.detail)
      : watchlistQuery.error != null
        ? 'Не удалось загрузить список'
        : null

  const watchlistLoading = watchlistQuery.isPending && watchlistQuery.fetchStatus === 'fetching'

  const canLoadMoreCards = Boolean(cards?.next_cursor)
  const canLoadMoreWatchlist = Boolean(watchlist?.next_cursor)

  const ratedCardsLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      cardsEnabled &&
      canLoadMoreCards &&
      (cards?.items.length ?? 0) > 0,
    isBusy: cardsQuery.isFetchingNextPage,
    onLoadMore: () => void cardsQuery.fetchNextPage(),
  })

  const watchlistLoadMoreRef = useInfiniteScrollLoadMore({
    enabled:
      authReady &&
      mainTab === 'movies' &&
      moviesSegment === 'watchlist' &&
      canLoadMoreWatchlist &&
      (watchlist?.items.length ?? 0) > 0,
    isBusy: watchlistQuery.isFetchingNextPage,
    onLoadMore: () => void watchlistQuery.fetchNextPage(),
  })

  return {
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
  }
}
