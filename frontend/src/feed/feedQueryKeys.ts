import type { GlobalFeedKind } from '../api/profileTypes'

/** Корень ключа бесконечной ленты — частичная инвалидация после создания карточки/поста. */
export const globalFeedQueryRootKey = ['globalFeed'] as const

export const globalFeedQueryKey = (kind: GlobalFeedKind, excludeOwn: boolean) =>
  ['globalFeed', kind, excludeOwn] as const

/** Теги с моих карточек (автодополнение при создании карточки). */
export const myMovieCardTagStatsQueryKey = () => ['myMovieCardTagStats'] as const

/** Кастомные теги с карточек пользователя (фильтр в профиле). */
export const userMovieCardTagStatsQueryKey = (userId: string) =>
  ['userMovieCardTagStats', userId] as const

/** Полки текущего пользователя (`GET /api/me/card-categories`). */
export const myCardCategoriesQueryKey = () => ['myCardCategories'] as const

/** Полки выбранного пользователя для публичного профиля (`GET /api/users/:id/card-categories`). */
export const publicProfileCardCategoriesQueryKey = (userId: string) =>
  ['publicProfileCardCategories', userId] as const
