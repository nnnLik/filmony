import { apiJson } from './client'

export type GenreCatalogItem = {
  slug: string
  genre: string
  films_count: number
}

export type GenresCatalogPage = {
  items: GenreCatalogItem[]
  next_cursor: string | null
}

export type GenreSummary = {
  slug: string
  genre: string
  films_count: number
  avg_community_rating: number | null
  top_genres: string[]
}

export type GenreFilmItem = {
  film_id: number
  title: string
  year: number | null
  poster_url: string | null
  genres: string[]
  community_avg_rating: number | null
  ratings_count: number
  my_card_id: number | null
}

export type GenreFilmsPage = {
  items: GenreFilmItem[]
  next_cursor: string | null
}

export async function getGenresCatalogPage(
  params: { cursor?: string | null; limit?: number } = {},
): Promise<GenresCatalogPage> {
  const q = new URLSearchParams()
  if (params.cursor != null && params.cursor !== '') {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<GenresCatalogPage>(`/api/genres${suffix}`)
}

export async function getGenreSummary(slug: string): Promise<GenreSummary> {
  return apiJson<GenreSummary>(`/api/genres/${encodeURIComponent(slug.trim())}`)
}

export async function getGenreFilmsPage(
  slug: string,
  params: { cursor?: string | null; limit?: number } = {},
): Promise<GenreFilmsPage> {
  const q = new URLSearchParams()
  if (params.cursor != null && params.cursor !== '') {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<GenreFilmsPage>(`/api/genres/${encodeURIComponent(slug.trim())}/films${suffix}`)
}
