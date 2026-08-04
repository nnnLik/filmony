import { apiJson } from './client'

export type DirectorSummary = {
  kinopoisk_id: number
  name: string
  films_count: number
  avg_community_rating: number | null
}

export type DirectorFilmItem = {
  film_id: number
  title: string
  year: number | null
  poster_url: string | null
  genres: string[]
  community_avg_rating: number | null
  ratings_count: number
  my_card_id: number | null
}

export type DirectorFilmsPage = {
  items: DirectorFilmItem[]
  next_cursor: string | null
}

export type DirectorCatalogItem = {
  kinopoisk_id: number
  name: string
  films_count: number
}

export type DirectorsCatalogPage = {
  items: DirectorCatalogItem[]
  next_cursor: string | null
}

export async function getDirectorsCatalogPage(
  params: { cursor?: string | null; limit?: number } = {},
): Promise<DirectorsCatalogPage> {
  const q = new URLSearchParams()
  if (params.cursor != null && params.cursor !== '') {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<DirectorsCatalogPage>(`/api/directors${suffix}`)
}

export async function getDirectorSummary(kinopoiskId: number): Promise<DirectorSummary> {
  return apiJson<DirectorSummary>(`/api/directors/${encodeURIComponent(String(kinopoiskId))}`)
}

export async function getDirectorFilmsPage(
  kinopoiskId: number,
  params: { cursor?: string | null; limit?: number } = {},
): Promise<DirectorFilmsPage> {
  const q = new URLSearchParams()
  if (params.cursor != null && params.cursor !== '') {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<DirectorFilmsPage>(
    `/api/directors/${encodeURIComponent(String(kinopoiskId))}/films${suffix}`,
  )
}
