/**
 * Типы элементов `kind: 'feed_post'` в ответе GET /api/cards/feed.
 * Вынесены в отдельный файл, чтобы не тащить весь `profileTypes` в парсер ESLint/IDE
 * и сохранить ациклический импорт (`profileTypes` реэкспортирует эти типы).
 */

/** Должен совпадать по значениям с `FeedCardSource` в `profileTypes`. */
export type FeedInFeedCardSource =
  | 'subscriptions'
  | 'subscribers'
  | 'personal_affinity'
  | 'discovery'
  | 'feed_posts'

/** Совпадает по полям с `MovieCardCommentAuthor` (структурная совместимость). */
export type FeedPostAuthorInFeed = {
  id: string
  profile_slug: string
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
  display_name: string | null
}

export type FeedPostReferencedCard = {
  movie_card_id: number
  film_title: string
  film_year: number | null
  film_poster_url: string | null
  rating: number
}

export type FeedPostInFeed = {
  kind: 'feed_post'
  id: number
  user_id: string
  author: FeedPostAuthorInFeed
  body: string
  image_url: string | null
  referenced_movie_card_id: number | null
  source_comment_id: number | null
  created_at: string
  feed_source: FeedInFeedCardSource
  referenced_card: FeedPostReferencedCard | null
}

/** GET /api/users/:id/feed-posts */
export type UserFeedPostsPage = {
  items: FeedPostInFeed[]
  next_cursor: string | null
}
