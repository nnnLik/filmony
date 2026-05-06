import { apiJson } from './client'
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

export async function createMovieCard(body: CreateMovieCardPayload): Promise<MovieCard> {
  return apiJson<MovieCard>('/api/cards', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
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
