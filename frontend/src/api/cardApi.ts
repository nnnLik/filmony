import { ApiError, apiFetch, apiJson } from './client'
import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  FeedMovieCardPage,
  Film,
  FollowingRatingsResponse,
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

export async function getFollowingRatingsForCard(cardId: number): Promise<FollowingRatingsResponse> {
  return apiJson<FollowingRatingsResponse>(`/api/cards/${cardId}/following-ratings`)
}

export async function getMovieCardFeedPage(params?: {
  cursor?: string | null
  limit?: number
}): Promise<FeedMovieCardPage> {
  const search = new URLSearchParams()
  if (params?.cursor) search.set('cursor', params.cursor)
  if (params?.limit != null) search.set('limit', String(params.limit))
  const suffix = search.toString()
  return apiJson<FeedMovieCardPage>(`/api/cards/feed${suffix ? `?${suffix}` : ''}`)
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

/** Fetches every comment for the card (flat list, oldest first), following `next_cursor` until exhausted. */
export async function listAllMovieCardComments(cardId: number): Promise<MovieCardComment[]> {
  const all: MovieCardComment[] = []
  let cursor: string | null | undefined
  const maxPages = 500
  for (let page = 0; page < maxPages; page++) {
    const chunk = await getMovieCardComments(cardId, {
      cursor: cursor ?? undefined,
      limit: 50,
    })
    all.push(...chunk.items)
    if (chunk.next_cursor == null || chunk.items.length === 0) break
    cursor = chunk.next_cursor
  }
  return all
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

export type ShareMovieCardResponse = {
  queued: number
}

export async function shareMovieCardWithFollowers(
  cardId: number,
  recipientUserIds: string[]
): Promise<ShareMovieCardResponse> {
  return apiJson<ShareMovieCardResponse>(`/api/cards/${cardId}/share`, {
    method: 'POST',
    body: JSON.stringify({ recipient_user_ids: recipientUserIds }),
    headers: { 'Content-Type': 'application/json' },
  })
}
