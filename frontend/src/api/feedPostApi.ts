import { ApiError, apiFetch, apiJson } from './client'
import { readHttpErrorDetail } from './readHttpErrorDetail'
import type {
  FeedPostComment,
  FeedPostCommentPage,
  FeedPostPayload,
} from './profileTypes'
import type { ReferencedInlineMovieCardSnippet, ReferencedMentionSnippet } from './inlineReferenceSnippetTypes'
import type {
  FeedPostAuthorInFeed,
  FeedPostInFeed,
  FeedPostSourceCommentInFeed,
} from './feedInFeedTypes'

export type CreateFeedPostBody = {
  body?: string
  image_url?: string | null
  referenced_movie_card_id?: number | null
  source_comment_id?: number | null
}

export async function uploadFeedPostImage(file: File): Promise<string> {
  const form = new FormData()
  form.append('file', file)
  const res = await apiFetch('/api/feed-posts/upload', {
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

function parseFeedPostSourceComment(raw: unknown): FeedPostSourceCommentInFeed | null {
  if (raw == null || typeof raw !== 'object') return null
  const o = raw as Record<string, unknown>
  const id = typeof o.id === 'number' ? o.id : Number(o.id)
  if (!Number.isFinite(id)) return null
  const text = typeof o.text === 'string' ? o.text : ''
  const au = o.author
  if (au == null || typeof au !== 'object') return null
  const a = au as Record<string, unknown>
  let authorId = ''
  if (typeof a.id === 'string') {
    authorId = a.id
  } else if (typeof a.id === 'number' && Number.isFinite(a.id)) {
    authorId = String(a.id)
  }
  if (authorId === '') return null
  const author: FeedPostAuthorInFeed = {
    id: authorId,
    profile_slug: typeof a.profile_slug === 'string' ? a.profile_slug : '',
    username: typeof a.username === 'string' ? a.username : null,
    first_name: typeof a.first_name === 'string' ? a.first_name : null,
    last_name: typeof a.last_name === 'string' ? a.last_name : null,
    photo_url: typeof a.photo_url === 'string' ? a.photo_url : null,
    display_name: typeof a.display_name === 'string' ? a.display_name : null,
  }
  const referenced_movie_cards = Array.isArray(o.referenced_movie_cards)
    ? (o.referenced_movie_cards as ReferencedInlineMovieCardSnippet[])
    : undefined
  const referenced_mentions = Array.isArray(o.referenced_mentions)
    ? (o.referenced_mentions as ReferencedMentionSnippet[])
    : undefined
  const imageUrlRaw = o.image_url
  const image_url =
    imageUrlRaw == null ? null : typeof imageUrlRaw === 'string' ? imageUrlRaw : null
  return {
    id,
    text,
    image_url,
    author,
    referenced_movie_cards,
    referenced_mentions,
  }
}

export async function createFeedPost(body: CreateFeedPostBody): Promise<FeedPostPayload> {
  return apiJson<FeedPostPayload>('/api/feed-posts', {
    method: 'POST',
    body: JSON.stringify({
      body: body.body ?? '',
      image_url: body.image_url ?? null,
      referenced_movie_card_id: body.referenced_movie_card_id ?? null,
      source_comment_id: body.source_comment_id ?? null,
    }),
    headers: { 'Content-Type': 'application/json' },
  })
}

export function normalizeFeedPostInFeed(raw: Record<string, unknown>): FeedPostInFeed {
  const commentsCount = typeof raw.comments_count === 'number' ? raw.comments_count : 0
  const preview = Array.isArray(raw.comments_preview) ? (raw.comments_preview as FeedPostComment[]) : []
  const source_comment = parseFeedPostSourceComment(raw.source_comment)
  return {
    ...(raw as unknown as FeedPostInFeed),
    kind: 'feed_post',
    comments_count: commentsCount,
    comments_preview: preview,
    source_comment: source_comment ?? undefined,
  }
}

export async function getFeedPostById(postId: number): Promise<FeedPostInFeed> {
  const raw = await apiJson<Record<string, unknown>>(`/api/feed-posts/${postId}`)
  return normalizeFeedPostInFeed(raw)
}

export async function listAllFeedPostComments(postId: number): Promise<FeedPostComment[]> {
  const acc: FeedPostComment[] = []
  let cursor: string | null = null
  for (;;) {
    const page = await getFeedPostComments(postId, { cursor, limit: 50 })
    acc.push(...page.items)
    if (page.next_cursor == null || page.next_cursor === '') {
      break
    }
    cursor = page.next_cursor
  }
  return acc
}

export async function getFeedPostComments(
  postId: number,
  params?: { cursor?: string | null; limit?: number },
): Promise<FeedPostCommentPage> {
  const search = new URLSearchParams()
  if (params?.cursor) search.set('cursor', params.cursor)
  if (params?.limit != null) search.set('limit', String(params.limit))
  const suffix = search.toString()
  return apiJson<FeedPostCommentPage>(
    `/api/feed-posts/${postId}/comments${suffix ? `?${suffix}` : ''}`,
  )
}

export async function createFeedPostComment(
  postId: number,
  body: { text: string; parent_comment_id?: number | null },
): Promise<FeedPostComment> {
  return apiJson<FeedPostComment>(`/api/feed-posts/${postId}/comments`, {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}

export async function updateFeedPostComment(
  postId: number,
  commentId: number,
  body: { text: string },
): Promise<FeedPostComment> {
  return apiJson<FeedPostComment>(`/api/feed-posts/${postId}/comments/${commentId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}

export async function deleteFeedPostComment(postId: number, commentId: number): Promise<void> {
  const res = await apiFetch(`/api/feed-posts/${postId}/comments/${commentId}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    throw new ApiError(res.status, await readHttpErrorDetail(res))
  }
}
