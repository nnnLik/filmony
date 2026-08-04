import { apiJson } from './client'

export type FranchiseSummary = {
  franchise_key: string
  label: string
  films_count: number
  avg_community_rating: number | null
}

export type FranchiseFilmItem = {
  film_id: number
  title: string
  year: number | null
  poster_url: string | null
  genres: string[]
  community_avg_rating: number | null
  ratings_count: number
  my_card_id: number | null
}

export type FranchiseFilmsPage = {
  items: FranchiseFilmItem[]
  next_cursor: string | null
}

function franchisePathSegment(franchiseKey: string): string {
  return encodeURIComponent(franchiseKey.trim())
}

export async function getFranchiseSummary(franchiseKey: string): Promise<FranchiseSummary> {
  return apiJson<FranchiseSummary>(`/api/franchises/${franchisePathSegment(franchiseKey)}`)
}

export async function getFranchiseFilmsPage(
  franchiseKey: string,
  params: { cursor?: string | null; limit?: number } = {},
): Promise<FranchiseFilmsPage> {
  const q = new URLSearchParams()
  if (params.cursor != null && params.cursor !== '') {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<FranchiseFilmsPage>(
    `/api/franchises/${franchisePathSegment(franchiseKey)}/films${suffix}`,
  )
}
