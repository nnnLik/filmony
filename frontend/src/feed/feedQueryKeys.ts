import type { FeedListMode } from '../api/profileTypes'

export const movieCardFeedQueryKey = (mode: FeedListMode) =>
  ['movieCardFeed', mode] as const

/** Теги с моих карточек (автодополнение при создании карточки). */
export const myMovieCardTagStatsQueryKey = () => ['myMovieCardTagStats'] as const

/** Кастомные теги с карточек пользователя (фильтр в профиле). */
export const userMovieCardTagStatsQueryKey = (userId: string) =>
  ['userMovieCardTagStats', userId] as const
