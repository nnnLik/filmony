import { ApiError, apiFetch, apiJson } from './client'
import { normalizeFeedPostInFeed } from './feedPostApi'
import type {
  CardCompany,
  CardMoodAfter,
  CardMoodBefore,
  MovieCardPage,
  MyMovieCardTagStatsResponse,
  MyProfile,
  MyUserCardCategory,
  MyUserCardCategoryListResponse,
  PublicProfile,
  SubscriptionListResponse,
  SubscriptionListType,
  UserMovieCardStats,
  WatchlistFilmItem,
  WatchlistFilmPage,
  WatchlistMembership,
} from './profileTypes'
import type { UserFeedPostsPage } from './feedInFeedTypes'

export type ProfileCardsSort = 'recent' | 'rating_desc' | 'rating_asc'

export type GetUserCardsParams = {
  cursor?: string | null
  limit?: number
  favoritesOnly?: boolean
  sort?: ProfileCardsSort
  /** Повторяется как `tag=` — пересечение на бэкенде */
  tags?: string[]
  yearMin?: number | null
  yearMax?: number | null
  company?: CardCompany | null
  moodBefore?: CardMoodBefore | null
  moodAfter?: CardMoodAfter | null
  /** Подстрока в отображаемом названии темы карточки пользователя. */
  filmTitle?: string | null
  /** Полка владельца списка; несовпадение id и владельца даёт 422 на бэкенде. */
  categoryId?: number | null
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

export async function getMyProfile(): Promise<MyProfile> {
  return apiJson<MyProfile>('/api/me/profile')
}

export async function getMyMovieCardTagStats(): Promise<MyMovieCardTagStatsResponse> {
  return apiJson<MyMovieCardTagStatsResponse>('/api/me/movie-card-tags')
}

export async function patchMyProfile(body: {
  display_name?: string | null
  bio?: string | null
}): Promise<MyProfile> {
  return apiJson<MyProfile>('/api/me/profile', {
    method: 'PATCH',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}

export async function getPublicProfileById(userId: string): Promise<PublicProfile> {
  return apiJson<PublicProfile>(`/api/users/${encodeURIComponent(userId)}`)
}

export async function getUserCards(userId: string, params: GetUserCardsParams): Promise<MovieCardPage> {
  const q = new URLSearchParams()
  if (params.cursor) {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  if (params.favoritesOnly === true) {
    q.set('favorites_only', 'true')
  }
  const sort = params.sort ?? 'recent'
  q.set('sort', sort)
  for (const t of params.tags ?? []) {
    const s = t.trim()
    if (s !== '') {
      q.append('tag', s)
    }
  }
  if (params.yearMin != null) {
    q.set('year_min', String(params.yearMin))
  }
  if (params.yearMax != null) {
    q.set('year_max', String(params.yearMax))
  }
  if (params.company != null) {
    q.set('company', params.company)
  }
  if (params.moodBefore != null) {
    q.set('mood_before', params.moodBefore)
  }
  if (params.moodAfter != null) {
    q.set('mood_after', params.moodAfter)
  }
  if (params.filmTitle != null && params.filmTitle.trim() !== '') {
    q.set('film_title', params.filmTitle.trim())
  }
  if (params.categoryId != null && params.categoryId >= 1) {
    q.set('category_id', String(params.categoryId))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<MovieCardPage>(`/api/users/${encodeURIComponent(userId)}/cards${suffix}`)
}

export async function getMyCardCategories(): Promise<MyUserCardCategoryListResponse> {
  return apiJson<MyUserCardCategoryListResponse>('/api/me/card-categories')
}

export async function createMyCardCategory(body: { name: string }): Promise<MyUserCardCategory> {
  return apiJson<MyUserCardCategory>('/api/me/card-categories', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}

export async function renameMyCardCategory(
  categoryId: number,
  body: { name: string },
): Promise<MyUserCardCategory> {
  return apiJson<MyUserCardCategory>(
    `/api/me/card-categories/${encodeURIComponent(String(categoryId))}`,
    {
      method: 'PATCH',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json' },
    },
  )
}

export async function getUserMovieCardTags(userId: string): Promise<MyMovieCardTagStatsResponse> {
  return apiJson<MyMovieCardTagStatsResponse>(
    `/api/users/${encodeURIComponent(userId)}/movie-card-tags`,
  )
}

export async function getUserFeedPosts(
  userId: string,
  params: { cursor?: string | null; limit?: number },
): Promise<UserFeedPostsPage> {
  const q = new URLSearchParams()
  if (params.cursor) {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  const body = await apiJson<{ items: Record<string, unknown>[]; next_cursor: string | null }>(
    `/api/users/${encodeURIComponent(userId)}/feed-posts${suffix}`,
  )
  return {
    next_cursor: body.next_cursor,
    items: body.items.map((it) => normalizeFeedPostInFeed(it)),
  }
}

export async function getUserWatchlist(
  userId: string,
  params: { cursor?: string | null; limit?: number },
): Promise<WatchlistFilmPage> {
  const q = new URLSearchParams()
  if (params.cursor) {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  return apiJson<WatchlistFilmPage>(
    `/api/users/${encodeURIComponent(userId)}/watchlist${suffix}`,
  )
}

export async function getUserMovieCardStats(userId: string): Promise<UserMovieCardStats> {
  return apiJson<UserMovieCardStats>(`/api/users/${encodeURIComponent(userId)}/stats`)
}

export async function postMyWatchlistFilm(filmId: number): Promise<WatchlistFilmItem> {
  return apiJson<WatchlistFilmItem>('/api/me/watchlist', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ film_id: filmId }),
  })
}

export async function deleteMyWatchlistFilm(filmId: number): Promise<void> {
  const res = await apiFetch(`/api/me/watchlist/films/${encodeURIComponent(String(filmId))}`, {
    method: 'DELETE',
  })
  await assertActionOk(res)
}

export async function getMyWatchlistFilmPresence(filmId: number): Promise<WatchlistMembership> {
  return apiJson<WatchlistMembership>(
    `/api/me/watchlist/films/${encodeURIComponent(String(filmId))}`,
  )
}

export async function authTelegram(initData: string): Promise<Response> {
  return apiFetch('/api/auth/telegram', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ initData }),
  })
}

export async function subscribeToUser(userId: string): Promise<void> {
  const res = await apiFetch(`/api/users/${encodeURIComponent(userId)}/subscriptions`, {
    method: 'POST',
  })
  await assertActionOk(res)
}

export async function unsubscribeFromUser(userId: string): Promise<void> {
  const res = await apiFetch(`/api/users/${encodeURIComponent(userId)}/subscriptions`, {
    method: 'DELETE',
  })
  await assertActionOk(res)
}

export async function getUserSubscriptions(
  userId: string,
  type: SubscriptionListType,
): Promise<SubscriptionListResponse> {
  const q = new URLSearchParams({ type })
  return apiJson<SubscriptionListResponse>(
    `/api/users/${encodeURIComponent(userId)}/subscriptions?${q.toString()}`,
  )
}

export type MovieCardsExportCsvResponse = {
  status: string
}

export async function postExportMyCardsCsv(): Promise<MovieCardsExportCsvResponse> {
  return apiJson<MovieCardsExportCsvResponse>('/api/me/cards/export-csv', {
    method: 'POST',
  })
}
