import { apiJson } from './client'

export type ActorSummary = {
  kinopoisk_id: number
  name: string
  poster_url: string | null
  films_count: number
}

export type ActorFilmItem = {
  film_id: number
  title: string
  year: number | null
  poster_url: string | null
  genres: string[]
  role: string | null
  my_card_id: number | null
  rating: number | null
  rated_at: string | null
}

export type ActorFilmsPage = {
  items: ActorFilmItem[]
  next_cursor: string | null
}

export async function getActorSummary(
  kinopoiskId: number,
  params: { userId?: string | null } = {},
): Promise<ActorSummary> {
  const q = new URLSearchParams()
  if (params.userId != null && params.userId.trim() !== '') {
    q.set('user_id', params.userId.trim())
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<ActorSummary>(`/api/actors/${encodeURIComponent(String(kinopoiskId))}${suffix}`)
}

export async function getActorFilmsPage(
  kinopoiskId: number,
  params: { cursor?: string | null; limit?: number; userId?: string | null } = {},
): Promise<ActorFilmsPage> {
  const q = new URLSearchParams()
  if (params.cursor != null && params.cursor !== '') {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  if (params.userId != null && params.userId.trim() !== '') {
    q.set('user_id', params.userId.trim())
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<ActorFilmsPage>(
    `/api/actors/${encodeURIComponent(String(kinopoiskId))}/films${suffix}`,
  )
}
