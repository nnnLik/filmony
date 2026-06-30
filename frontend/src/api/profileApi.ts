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
  WatchlistEntryItem,
  WatchlistEntryPage,
  WatchlistMembership,
  PlannedUserCard,
  WatchTag,
} from './profileTypes'

export type { WatchTag } from './profileTypes'
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

export type CreateWatchlistEntryBody = {
  film_id?: number
  catalog_item_id?: number
  card_id?: string
  provider_meta?: Record<string, unknown>
  watch_tag?: WatchTag
  company?: CardCompany
  category_id?: number | null
  watch_note?: string
  watch_with_user_id?: string | null
  watch_with_user_ids?: string[]
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

function normalizeWatchlistEntry(raw: WatchlistEntryItem): WatchlistEntryItem {
  const title = raw.title || raw.film_title || 'Untitled'
  const poster = raw.poster_url ?? raw.film_poster_url ?? null
  const year = raw.year ?? raw.film_year ?? null
  return {
    ...raw,
    title,
    poster_url: poster,
    year,
    film_genres: raw.film_genres ?? [],
  }
}

function normalizeWatchlistPage(body: WatchlistEntryPage): WatchlistEntryPage {
  return {
    next_cursor: body.next_cursor,
    items: body.items.map((it) => normalizeWatchlistEntry(it)),
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

/** Полки пользователя для фильтра в чужом (и своём через публичный URL) профиле. */
export async function getUserPublicCardCategories(
  userId: string,
): Promise<MyUserCardCategoryListResponse> {
  return apiJson<MyUserCardCategoryListResponse>(
    `/api/users/${encodeURIComponent(userId)}/card-categories`,
  )
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
): Promise<WatchlistEntryPage> {
  const q = new URLSearchParams()
  if (params.cursor) {
    q.set('cursor', params.cursor)
  }
  if (params.limit != null) {
    q.set('limit', String(params.limit))
  }
  const suffix = q.toString() ? `?${q.toString()}` : ''
  const body = await apiJson<WatchlistEntryPage>(
    `/api/users/${encodeURIComponent(userId)}/watchlist${suffix}`,
  )
  return normalizeWatchlistPage(body)
}

export async function getUserMovieCardStats(userId: string): Promise<UserMovieCardStats> {
  return apiJson<UserMovieCardStats>(`/api/users/${encodeURIComponent(userId)}/stats`)
}

export async function postCreateWatchlistEntry(body: CreateWatchlistEntryBody): Promise<WatchlistEntryItem> {
  const raw = await apiJson<WatchlistEntryItem>('/api/me/watchlist', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return normalizeWatchlistEntry(raw)
}

export type GetMyPlannedCardParams = {
  card_id?: string
  film_id?: number
  catalog_item_id?: number
}

export async function getMyPlannedCard(params: GetMyPlannedCardParams): Promise<PlannedUserCard> {
  const q = new URLSearchParams()
  if (params.card_id != null && params.card_id !== '') {
    q.set('card_id', params.card_id)
  }
  if (params.film_id != null && params.film_id > 0) {
    q.set('film_id', String(params.film_id))
  }
  if (params.catalog_item_id != null && params.catalog_item_id > 0) {
    q.set('catalog_item_id', String(params.catalog_item_id))
  }
  return apiJson<PlannedUserCard>(`/api/me/planned-card?${q.toString()}`)
}

/** @deprecated Use postCreateWatchlistEntry({ film_id }) */
export async function postMyWatchlistFilm(filmId: number): Promise<WatchlistEntryItem> {
  return postCreateWatchlistEntry({ film_id: filmId })
}

export async function patchMyWatchlistEntry(
  entryId: number,
  body: { watch_tag: WatchTag },
): Promise<{ id: number; watch_tag: string }> {
  return apiJson<{ id: number; watch_tag: string }>(
    `/api/watchlist/${encodeURIComponent(String(entryId))}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  )
}

export async function deleteMyWatchlistEntry(entryId: number): Promise<void> {
  const res = await apiFetch(`/api/me/watchlist/${encodeURIComponent(String(entryId))}`, {
    method: 'DELETE',
  })
  await assertActionOk(res)
}

export async function deleteMyWatchlistFilm(filmId: number): Promise<void> {
  const res = await apiFetch(`/api/me/watchlist/films/${encodeURIComponent(String(filmId))}`, {
    method: 'DELETE',
  })
  await assertActionOk(res)
}

export async function getMyWatchlistPresence(cardId: string): Promise<WatchlistMembership> {
  const q = new URLSearchParams({ card_id: cardId })
  return apiJson<WatchlistMembership>(`/api/me/watchlist/presence?${q.toString()}`)
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
