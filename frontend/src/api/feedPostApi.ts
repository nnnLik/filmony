import { ApiError, apiFetch, apiJson } from './client'
import { readHttpErrorDetail } from './readHttpErrorDetail'
import type { FeedPostPayload } from './profileTypes'

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
