export type CollectionKind = 'evergreen' | 'seasonal'

export type UserCollectionProgress = {
  rated_count: number
  total_count: number
  completed_at: string | null
}

export type CollectionSummary = {
  slug: string
  kind: CollectionKind
  title: string
  description: string | null
  season_year: number | null
  film_count: number
  content_updated_at: string
  viewer_progress: UserCollectionProgress | null
  is_pinned: boolean | null
}

export type CollectionListResponse = {
  items: CollectionSummary[]
}

export type CollectionFilmItem = {
  film_id: number
  title: string
  year: number | null
  poster_url: string | null
  viewer_has_rated: boolean | null
  viewer_card_id: number | null
}

export type CollectionFilmsPage = {
  items: CollectionFilmItem[]
  next_cursor: string | null
  total_count: number
}

export type ProfilePinnedCollectionsResponse = {
  items: CollectionSummary[]
}
