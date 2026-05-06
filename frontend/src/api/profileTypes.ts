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

export type CardCompany = 'alone' | 'partner' | 'friends' | 'family'
export type CardMoodBefore = 'relax' | 'laugh' | 'sad' | 'thrill'
export type CardMoodAfter = 'laughed' | 'cried' | 'enjoyed' | 'tense' | 'wasted_time'

export type ReactionCountItem = {
  reaction_type_id: number
  count: number
  image_url: string
  label: string | null
}

export type ReactionSummary = {
  counts: ReactionCountItem[]
  my_reaction_type_ids: number[]
}

export type ReactionCatalogItem = {
  id: number
  label: string | null
  image_url: string
  category_slug?: string | null
  asset_key?: string | null
}

export type ReactionCatalogTab = {
  category_slug: string
  label: string
  items: ReactionCatalogItem[]
}

export type ReactionGroupedCatalog = {
  recent: ReactionCatalogItem[]
  tabs: ReactionCatalogTab[]
}

export type ReactionActor = {
  id: string
  profile_slug: string
  display_name: string | null
  username: string | null
  first_name: string | null
  last_name: string | null
  photo_url: string | null
}

export type ReactionActorsResponse = {
  items: ReactionActor[]
}

export type MovieCard = {
  id: number
  user_id?: string
  film_id: number
  film_kinopoisk_id: number
  film_genres: string[]
  film_title: string
  film_year: number | null
  film_poster_url: string | null
  rating: number
  company: CardCompany
  mood_before: CardMoodBefore
  mood_after: CardMoodAfter
  custom_tags: string[]
  reactions?: ReactionSummary
}

/** Карточка ленты: поля фильма и автора из GET /api/cards/feed */
export type FeedMovieCard = MovieCard & {
  user_id: string
  card_author: MovieCardCommentAuthor
  comments_count: number
  comments_preview: MovieCardComment[]
}

export type FeedMovieCardPage = {
  items: FeedMovieCard[]
  next_cursor: string | null
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

export type MovieCardComment = {
  id: number
  movie_card_id: number
  parent_comment_id: number | null
  text: string
  created_at: string
  replies_count: number
  total_descendants_count: number
  author: MovieCardCommentAuthor
  reactions?: ReactionSummary
}

export type MovieCardCommentPage = {
  items: MovieCardComment[]
  next_cursor: string | null
}

export type Film = {
  id: number
  kinopoisk_id: number
  genres: string[]
  title: string
  year: number | null
  poster_url: string | null
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
