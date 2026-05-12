import type {
  ReferencedInlineMovieCardSnippet,
  ReferencedMentionSnippet,
} from './inlineReferenceSnippetTypes'

export type {
  ReferencedInlineMovieCardSnippet,
  ReferencedMentionSnippet,
} from './inlineReferenceSnippetTypes'

export type MyMovieCardTagStatItem = {
  tag: string
  use_count: number
}

export type MyMovieCardTagStatsResponse = {
  items: MyMovieCardTagStatItem[]
}

export type MyProfile = {
  id: string
  telegram_user_id: number
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
  language_code: string | null
  profile_slug: string
  display_name: string | null
  bio: string | null
  cards_count: number
  favorites_count: number
  watchlist_count: number
  friends_count: number
  followers_count: number
  following_count: number
}

export type PublicProfile = {
  id: string
  profile_slug: string
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
  display_name: string | null
  bio: string | null
  cards_count: number
  favorites_count: number
  watchlist_count: number
  friends_count: number
  followers_count: number
  following_count: number
}

export type SubscriptionListType = 'followers' | 'following' | 'both'
export type SubscriptionRelationType = 'follower' | 'following'

export type SubscriptionListItem = {
  id: string
  profile_slug: string
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
  display_name: string | null
  relation_type: SubscriptionRelationType
}

export type SubscriptionListResponse = {
  items: SubscriptionListItem[]
}

export type MovieCardPage = {
  items: MovieCard[]
  next_cursor: string | null
}

export type WatchlistFilmItem = {
  film_id: number
  film_kinopoisk_id: number
  film_genres: string[]
  film_title: string
  film_year: number | null
  film_poster_url: string | null
}

export type WatchlistFilmPage = {
  items: WatchlistFilmItem[]
  next_cursor: string | null
}

export type WatchlistMembership = {
  in_watchlist: boolean
}

export type CardCompany = 'alone' | 'partner' | 'friends' | 'family'
export type CardMoodBefore = 'relax' | 'laugh' | 'sad' | 'thrill'
export type CardMoodAfter = 'laughed' | 'cried' | 'enjoyed' | 'tense' | 'wasted_time'

export type ReactionActor = {
  id: string
  profile_slug: string
  display_name: string | null
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
}

export type ReactionCountItem = {
  reaction_type_id: number
  count: number
  image_url: string
  asset_key: string
  /** Кто поставил эту реакцию (ограниченный список; при большем `count` есть ещё реакции). */
  reactors: ReactionActor[]
}

export type ReactionSummary = {
  counts: ReactionCountItem[]
  my_reaction_type_ids: number[]
}

export type ReactionCatalogItem = {
  id: number
  image_url: string
  category_slug: string
  asset_key: string
}

export type ReactionCatalogTab = {
  category_slug: string
  label: string
  items: ReactionCatalogItem[]
}

export type ReactionGroupedCatalog = {
  tabs: ReactionCatalogTab[]
}

export type MovieCardCommentAuthor = {
  id: string
  profile_slug: string
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
  display_name: string | null
}

export type MovieCard = {
  id: number
  user_id?: string
  /** Приходит в GET /api/cards/:id и в элементах ленты; может отсутствовать в укороченных ответах. */
  card_author?: MovieCardCommentAuthor
  film_id: number
  film_kinopoisk_id: number
  film_genres: string[]
  film_title: string
  film_year: number | null
  film_poster_url: string | null
  /** Только GET /api/cards/:id (не в ленте). */
  film_short_description?: string | null
  film_description?: string | null
  rating: number
  company: CardCompany
  mood_before: CardMoodBefore
  mood_after: CardMoodAfter
  custom_tags: string[]
  /** Заметка о просмотре (до 500 символов); в ленте и профиле приходит с бэкенда. */
  watch_note?: string
  reactions?: ReactionSummary
  is_favorite?: boolean
}

/** Query-параметр `mode` для GET /api/cards/feed (legacy) */
export type FeedListMode = 'default' | 'subscriptions_only' | 'subscribers_only'

/** Вкладка GET /api/feed/global */
export type GlobalFeedKind = 'all' | 'posts' | 'cards'

/** Источник элемента в ленте (legacy + глобальная лента) */
export type FeedCardSource =
  | 'subscriptions'
  | 'subscribers'
  | 'personal_affinity'
  | 'discovery'
  | 'feed_posts'
  | 'own_cards'
  | 'global'

/** Карточка ленты: данные тайтла и автора из GET /api/cards/feed */
export type FeedMovieCard = MovieCard & {
  kind: 'movie_card'
  user_id: string
  feed_source: FeedCardSource
  card_author: MovieCardCommentAuthor
  comments_count: number
  comments_preview: MovieCardComment[]
}

/** Ответ POST /api/feed-posts */
export type FeedPostPayload = {
  id: number
  user_id: string
  body: string
  image_url: string | null
  referenced_movie_card_id: number | null
  source_comment_id: number | null
  created_at: string
}

export type FollowingRatingEntry = {
  user_id: string
  movie_card_id: number
  profile_slug: string
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
  display_name: string | null
  rating: number
}

export type FollowingRatingsResponse = {
  /** Ваша оценка этого тайтла, если открыта чужая карточка и карточка есть у вас. */
  viewer_rating: FollowingRatingEntry | null
  items: FollowingRatingEntry[]
}

export type MovieCardComment = {
  id: number
  movie_card_id: number
  parent_comment_id: number | null
  text: string
  image_url?: string | null
  created_at: string
  replies_count: number
  total_descendants_count: number
  author: MovieCardCommentAuthor
  reactions?: ReactionSummary
  referenced_movie_cards?: ReferencedInlineMovieCardSnippet[]
  referenced_mentions?: ReferencedMentionSnippet[]
}

export type MovieCardCommentPage = {
  items: MovieCardComment[]
  next_cursor: string | null
}

/** Комментарий к текстовому посту ленты (GET/POST `/api/feed-posts/:id/comments`). */
export type FeedPostComment = {
  id: number
  feed_post_id: number
  parent_comment_id: number | null
  text: string
  created_at: string
  replies_count: number
  total_descendants_count: number
  author: MovieCardCommentAuthor
  reactions?: ReactionSummary
  referenced_movie_cards?: ReferencedInlineMovieCardSnippet[]
  referenced_mentions?: ReferencedMentionSnippet[]
}

export type FeedPostCommentPage = {
  items: FeedPostComment[]
  next_cursor: string | null
}

export type Film = {
  id: number
  kinopoisk_id: number
  genres: string[]
  title: string
  year: number | null
  poster_url: string | null
  short_description?: string | null
  description?: string | null
  /** Present when the API knows the viewer already has a card for this film. */
  my_card_id?: number | null
}

export type FilmCommunityAuthor = {
  id: string
  profile_slug: string
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
  display_name: string | null
}

export type FilmCommunityCardItem = {
  id: number
  author: FilmCommunityAuthor
  rating: number
  company: CardCompany
  mood_before: CardMoodBefore
  mood_after: CardMoodAfter
  watch_note: string
  custom_tags: string[]
  updated_at: string
  is_favorite: boolean
}

export type FilmCommunityCardsPage = {
  items: FilmCommunityCardItem[]
  next_cursor: string | null
}

export type RatingDistributionItem = {
  rating: number
  count: number
}

export type YearDistributionItem = {
  year: number
  count: number
}

export type ValueDistributionItem = {
  value: string
  count: number
}

export type TagDistributionItem = {
  tag: string
  count: number
}

export type ProfileStatsMovieItem = {
  card_id: number
  film_id: number
  film_title: string
  film_year: number | null
  film_poster_url: string | null
  rating: number
}

export type UserMovieCardStats = {
  total_movies: number
  average_rating: number
  rating_distribution: RatingDistributionItem[]
  year_distribution: YearDistributionItem[]
  popular_tags: TagDistributionItem[]
  watch_with_distribution: ValueDistributionItem[]
  mood_after_distribution: ValueDistributionItem[]
  top_movies: ProfileStatsMovieItem[]
  worst_movies: ProfileStatsMovieItem[]
}
