import { apiJson } from './client'

export type SearchCardItem = {
  card_id: number
  title: string
  year: number | null
  poster_url: string | null
  summary: string | null
  rating: number
  author_profile_slug: string
  author_display_name: string | null
  author_username: string | null
}

export type SearchFilmItem = SearchCardItem

/** Catalog title in search without an existing user card (legacy `films` array). */
export type SearchFilmHit = {
  film_id?: number | null
  catalog_item_id?: number | null
  kind?: 'film' | 'game' | null
  /** Present when legacy API duplicates `cards` into `films`. */
  card_id?: number
  title: string
  year: number | null
  poster_url: string | null
  summary: string | null
}

/** Catalog item (film or game) without a user card in search results. */
export type SearchCatalogItemHit = {
  catalog_item_id: number
  kind: 'film' | 'game'
  title: string
  year: number | null
  poster_url: string | null
  summary: string | null
}

export type SearchUserItem = {
  id: string
  profile_slug: string
  username: string | null
  display_name: string | null
  photo_url: string | null
  movie_cards_count?: number
  average_rating?: number | null
}

export type SearchCatalogResponse = {
  cards?: SearchCardItem[]
  films?: SearchFilmHit[]
  catalog_items?: SearchCatalogItemHit[]
  users: SearchUserItem[]
}

export type SearchSuggestionsResponse = {
  mutual_circle: SearchUserItem[]
  popular_authors: SearchUserItem[]
  random_with_cards: SearchUserItem[]
}

export async function searchCatalog(
  q: string,
  params?: { limit_cards?: number; limit_films?: number; limit_users?: number },
): Promise<SearchCatalogResponse> {
  const trimmed = q.trim()
  const sp = new URLSearchParams({ q: trimmed })
  if (params?.limit_cards != null) {
    sp.set('limit_cards', String(params.limit_cards))
  }
  if (params?.limit_films != null) {
    sp.set('limit_films', String(params.limit_films))
  }
  if (params?.limit_users != null) {
    sp.set('limit_users', String(params.limit_users))
  }
  return apiJson<SearchCatalogResponse>(`/api/search?${sp.toString()}`)
}

export async function searchSuggestions(): Promise<SearchSuggestionsResponse> {
  return apiJson<SearchSuggestionsResponse>('/api/search/suggestions')
}
