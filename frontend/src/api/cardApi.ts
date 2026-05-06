import { ApiError, apiFetch, apiJson } from './client'
import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  Film,
  MovieCard,
  MovieCardComment,
  MovieCardCommentPage,
} from './profileTypes'

export type CreateMovieCardPayload = {
  film_id: number
  kinopoisk_id: number
  genres: string[]
  rating: number
  company: CardCompany
  mood_before: CardMoodBefore
  mood_after: CardMoodAfter
  custom_tags: string[]
}

export type UpdateMovieCardPayload = {
  rating?: number
  company?: CardCompany
  mood_before?: CardMoodBefore
  mood_after?: CardMoodAfter
  custom_tags?: string[]
}

export async function createMovieCard(body: CreateMovieCardPayload): Promise<MovieCard> {
  return apiJson<MovieCard>('/api/cards', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}

async function readActionErrorDetail(res: Response): Promise<unknown> {
  const ct = res.headers.get('content-type') ?? ''
  if (ct.includes('application/json')) {
    try {
      const body = (await res.json()) as { detail?: unknown }
      return body.detail ?? body
    } catch {
      return null
    }
  }
  return await res.text()
}

async function assertActionOk(res: Response): Promise<void> {
  if (!res.ok) {
    throw new ApiError(res.status, await readActionErrorDetail(res))
  }
}

export async function resolveFilmByKinopoiskUrl(url: string): Promise<Film> {
  return apiJson<Film>('/api/films/resolve', {
    method: 'POST',
    body: JSON.stringify({ url }),
    headers: { 'Content-Type': 'application/json' },
  })
}

export async function getFilmById(filmId: number): Promise<Film> {
  return apiJson<Film>(`/api/films/${filmId}`)
}

export async function getMovieCardById(cardId: number): Promise<MovieCard> {
  return apiJson<MovieCard>(`/api/cards/${cardId}`)
}

export const updateMovieCard: (cardId: number, body: UpdateMovieCardPayload) => Promise<MovieCard> = async (
  cardId: number,
  body: UpdateMovieCardPayload
) => {
  return apiJson<MovieCard>(`/api/cards/${cardId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}

export const deleteMovieCard: (cardId: number) => Promise<void> = async (cardId: number) => {
  const res = await apiFetch(`/api/cards/${cardId}`, {
    method: 'DELETE',
  })
  await assertActionOk(res)
}

export async function getMovieCardComments(
  cardId: number,
  params?: { cursor?: string | null; limit?: number }
): Promise<MovieCardCommentPage> {
  const search = new URLSearchParams()
  if (params?.cursor) search.set('cursor', params.cursor)
  if (params?.limit != null) search.set('limit', String(params.limit))
  const suffix = search.toString()
  return apiJson<MovieCardCommentPage>(`/api/cards/${cardId}/comments${suffix ? `?${suffix}` : ''}`)
}

export async function getMovieCardCommentReplies(
  cardId: number,
  commentId: number,
  params?: { cursor?: string | null; limit?: number }
): Promise<MovieCardCommentPage> {
  const search = new URLSearchParams()
  if (params?.cursor) search.set('cursor', params.cursor)
  if (params?.limit != null) search.set('limit', String(params.limit))
  const suffix = search.toString()
  return apiJson<MovieCardCommentPage>(
    `/api/cards/${cardId}/comments/${commentId}/replies${suffix ? `?${suffix}` : ''}`
  )
}

export async function createMovieCardComment(
  cardId: number,
  body: { text: string; parent_comment_id?: number | null }
): Promise<MovieCardComment> {
  return apiJson<MovieCardComment>(`/api/cards/${cardId}/comments`, {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}
