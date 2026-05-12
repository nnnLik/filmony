import { ApiError, apiFetch, apiJson } from './client'
import { readHttpErrorDetail } from './readHttpErrorDetail'
import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  FeedListMode,
  FeedMovieCard,
  FeedMovieCardPage,
  FeedPageItem,
  FeedPostComment,
  Film,
  FilmCommunityCardsPage,
  FollowingRatingsResponse,
  GlobalFeedKind,
  MovieCard,
  MovieCardComment,
  MovieCardCommentPage,
} from './profileTypes'
import type { FeedPostInFeed } from './feedInFeedTypes'

export type CreateMovieCardPayload = {
  film_id: number
  kinopoisk_id: number
  genres: string[]
  rating: number
  company: CardCompany
  mood_before: CardMoodBefore
  mood_after: CardMoodAfter
  custom_tags: string[]
  watch_note?: string
}

export type UpdateMovieCardPayload = {
  rating?: number
  company?: CardCompany
  mood_before?: CardMoodBefore
  mood_after?: CardMoodAfter
  custom_tags?: string[]
  watch_note?: string
  is_favorite?: boolean
}

export async function createMovieCard(body: CreateMovieCardPayload): Promise<MovieCard> {
  return apiJson<MovieCard>('/api/cards', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}

async function readActionErrorDetail(res: Response): Promise<unknown> {
  return readHttpErrorDetail(res)
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

export async function getFilmCommunityCardsPage(
  filmId: number,
  params?: { cursor?: string | null; limit?: number },
): Promise<FilmCommunityCardsPage> {
  const sp = new URLSearchParams()
  if (params?.cursor != null && params.cursor !== '') {
    sp.set('cursor', params.cursor)
  }
  if (params?.limit != null) {
    sp.set('limit', String(params.limit))
  }
  const q = sp.toString()
  return apiJson<FilmCommunityCardsPage>(`/api/films/${filmId}/community-cards${q ? `?${q}` : ''}`)
}

export async function getMovieCardById(cardId: number): Promise<MovieCard> {
  return apiJson<MovieCard>(`/api/cards/${cardId}`)
}

export async function getFollowingRatingsForCard(cardId: number): Promise<FollowingRatingsResponse> {
  return apiJson<FollowingRatingsResponse>(`/api/cards/${cardId}/following-ratings`)
}

function normalizeFeedPageItem(raw: Record<string, unknown>): FeedPageItem {
  if (raw.kind === 'feed_post') {
    const commentsCount = typeof raw.comments_count === 'number' ? raw.comments_count : 0
    const preview = Array.isArray(raw.comments_preview)
      ? (raw.comments_preview as FeedPostComment[])
      : []
    return {
      ...(raw as unknown as FeedPostInFeed),
      kind: 'feed_post',
      comments_count: commentsCount,
      comments_preview: preview,
    }
  }
  return { ...raw, kind: 'movie_card' as const } as FeedMovieCard
}

export async function getMovieCardFeedPage(params?: {
  cursor?: string | null
  limit?: number
  /** Совпадает с query `mode` на бэкенде; передавайте при пагинации тот же режим */
  mode?: FeedListMode
}): Promise<FeedMovieCardPage> {
  const search = new URLSearchParams()
  if (params?.cursor) search.set('cursor', params.cursor)
  if (params?.limit != null) search.set('limit', String(params.limit))
  if (params?.mode != null && params.mode !== 'default') search.set('mode', params.mode)
  const suffix = search.toString()
  const body = await apiJson<{
    items: Record<string, unknown>[]
    next_cursor: string | null
    feed_head_version?: number
  }>(`/api/cards/feed${suffix ? `?${suffix}` : ''}`)
  return {
    next_cursor: body.next_cursor,
    items: body.items.map(normalizeFeedPageItem),
    feed_head_version: typeof body.feed_head_version === 'number' ? body.feed_head_version : 0,
  }
}

/** Глобальная лента: GET /api/feed/global */
export async function getGlobalFeedPage(params?: {
  cursor?: string | null
  limit?: number
  kind?: GlobalFeedKind
  /** GET /api/feed/global?exclude_own=true — скрыть посты и карточки текущего пользователя */
  excludeOwn?: boolean
}): Promise<FeedMovieCardPage> {
  const search = new URLSearchParams()
  if (params?.cursor) search.set('cursor', params.cursor)
  if (params?.limit != null) search.set('limit', String(params.limit))
  const kind = params?.kind ?? 'all'
  if (kind !== 'all') search.set('kind', kind)
  if (params?.excludeOwn === true) search.set('exclude_own', 'true')
  const suffix = search.toString()
  const body = await apiJson<{
    items: Record<string, unknown>[]
    next_cursor: string | null
    feed_head_version?: number
  }>(`/api/feed/global${suffix ? `?${suffix}` : ''}`)
  return {
    next_cursor: body.next_cursor,
    items: body.items.map(normalizeFeedPageItem),
    feed_head_version: typeof body.feed_head_version === 'number' ? body.feed_head_version : 0,
  }
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

export async function uploadMovieCardCommentImage(file: File): Promise<string> {
  const form = new FormData()
  form.append('file', file)
  const res = await apiFetch('/api/cards/comment-images/upload', {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const detail: unknown = await readHttpErrorDetail(res)
    throw new ApiError(res.status, detail)
  }
  const data = (await res.json()) as { url?: string }
  if (typeof data.url !== 'string' || data.url.trim() === '') {
    throw new ApiError(res.status, 'invalid upload response')
  }
  return data.url.trim()
}

export async function createMovieCardComment(
  cardId: number,
  body: { text: string; parent_comment_id?: number | null; image_url?: string | null }
): Promise<MovieCardComment> {
  return apiJson<MovieCardComment>(`/api/cards/${cardId}/comments`, {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}

export type WatchedInlinePickerItem = {
  movie_card_id: number
  film_title: string
  film_year: number | null
}

export type WatchedInlinePickerListResponse = {
  items: WatchedInlinePickerItem[]
}

export async function listWatchedInlinePicker(params?: {
  q?: string
  limit?: number
}): Promise<WatchedInlinePickerListResponse> {
  const sp = new URLSearchParams()
  if (params?.q != null && params.q.trim() !== '') {
    sp.set('q', params.q.trim())
  }
  if (params?.limit != null) {
    sp.set('limit', String(params.limit))
  }
  const qs = sp.toString()
  return apiJson<WatchedInlinePickerListResponse>(
    `/api/cards/watched-inline-picker${qs ? `?${qs}` : ''}`,
  )
}

export type ShareMovieCardResponse = {
  queued: number
}

export async function shareMovieCardWithFollowers(
  cardId: number,
  recipientUserIds: string[],
  options?: { shareComment?: string }
): Promise<ShareMovieCardResponse> {
  return apiJson<ShareMovieCardResponse>(`/api/cards/${cardId}/share`, {
    method: 'POST',
    body: JSON.stringify({
      recipient_user_ids: recipientUserIds,
      share_comment: options?.shareComment?.trim() ?? '',
    }),
    headers: { 'Content-Type': 'application/json' },
  })
}
