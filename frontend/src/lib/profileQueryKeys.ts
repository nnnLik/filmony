/** Корень ключей профиля — частичная инвалидация после мутаций карточек/постов. */
export const profileQueryRootKey = ['profile'] as const

export const myProfileQueryKey = () => [...profileQueryRootKey, 'me'] as const

export const userPublicProfileQueryKey = (userId: string) =>
  [...profileQueryRootKey, 'public', userId] as const

/** Бесконечный список оценённых карточек; `ratedQueryKey` — сериализованный фильтр. */
export const userCardsQueryKey = (userId: string, ratedQueryKey: string) =>
  [...profileQueryRootKey, 'cards', userId, ratedQueryKey] as const

export const userWatchlistQueryKey = (userId: string) =>
  [...profileQueryRootKey, 'watchlist', userId] as const

export const userFeedPostsQueryKey = (userId: string) =>
  [...profileQueryRootKey, 'feedPosts', userId] as const

export const userFavoritesStripQueryKey = (userId: string) =>
  [...profileQueryRootKey, 'favoritesStrip', userId] as const

export const userMovieCardStatsQueryKey = (
  userId: string,
  activityCategoryId: number | null,
) => [...profileQueryRootKey, 'movieCardStats', userId, activityCategoryId] as const

export const myLatestMonthlyRecapQueryKey = () =>
  [...profileQueryRootKey, 'monthlyRecap'] as const

export const profileStatsFilteredRankingsQueryKey = (userId: string, ratedQueryKey: string) =>
  [...profileQueryRootKey, 'statsFilteredRankings', userId, ratedQueryKey] as const

export const userFollowingStatusQueryKey = (myUserId: string, targetUserId: string) =>
  [...profileQueryRootKey, 'followingStatus', myUserId, targetUserId] as const
