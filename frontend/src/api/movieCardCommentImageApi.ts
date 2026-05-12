import { ApiError, apiFetch } from './client'
import { readHttpErrorDetail } from './readHttpErrorDetail'

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
