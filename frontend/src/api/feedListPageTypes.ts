/**
 * Элементы страницы ленты (`FeedPageItem` / `FeedMovieCardPage`).
 * Вынесено из `profileTypes`, чтобы тот не импортировал `feedInFeedTypes` (цикл модулей).
 */

import type { FeedPostInFeed } from './feedInFeedTypes'
import type { FeedMovieCard } from './profileTypes'

export type FeedPageItem = FeedMovieCard | FeedPostInFeed

export type FeedMovieCardPage = {
  items: FeedPageItem[]
  next_cursor: string | null
  /** Версия головы глобальной ленты (GET /api/feed/global); для legacy-ленты может быть 0 */
  feed_head_version?: number
}
