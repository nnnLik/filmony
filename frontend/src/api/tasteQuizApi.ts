import { ApiError, apiJson, postJson, readErrorDetail } from './client'
import type {
  TasteQuizCanPlayResponse,
  TasteQuizCreateInviteResponse,
  TasteQuizKnowledgeBatchResponse,
  TasteQuizKnowledgeDirection,
  TasteQuizKnowledgeListResponse,
  TasteQuizResolveInviteResponse,
  TasteQuizSession,
  TasteQuizSubmitAnswerResponse,
} from './tasteQuizTypes'

export async function checkTasteQuizCanPlay(
  ownerId: string,
  inviteToken?: string | null,
): Promise<TasteQuizCanPlayResponse> {
  const params = new URLSearchParams({ owner_id: ownerId })
  if (inviteToken != null && inviteToken.trim() !== '') {
    params.set('invite_token', inviteToken.trim())
  }
  return apiJson<TasteQuizCanPlayResponse>(`/api/taste-quiz/can-play?${params.toString()}`)
}

export async function createTasteQuizSession(
  ownerId: string,
  inviteToken?: string | null,
): Promise<TasteQuizSession> {
  return apiJson<TasteQuizSession>('/api/taste-quiz/sessions', {
    method: 'POST',
    body: JSON.stringify({
      owner_id: ownerId,
      invite_token: inviteToken?.trim() ? inviteToken.trim() : null,
    }),
  })
}

export async function getTasteQuizSession(sessionId: string): Promise<TasteQuizSession> {
  return apiJson<TasteQuizSession>(`/api/taste-quiz/sessions/${encodeURIComponent(sessionId)}`)
}

export async function submitTasteQuizAnswer(
  sessionId: string,
  sessionCardId: string,
  guessRating: number,
): Promise<TasteQuizSubmitAnswerResponse> {
  return apiJson<TasteQuizSubmitAnswerResponse>(
    `/api/taste-quiz/sessions/${encodeURIComponent(sessionId)}/answers`,
    {
      method: 'POST',
      body: JSON.stringify({
        session_card_id: sessionCardId,
        guess_rating: guessRating,
      }),
    },
  )
}

export async function abandonTasteQuizSession(sessionId: string): Promise<TasteQuizSession> {
  const res = await postJson(`/api/taste-quiz/sessions/${encodeURIComponent(sessionId)}/abandon`, {})
  if (!res.ok) {
    throw new ApiError(res.status, await readErrorDetail(res))
  }
  return (await res.json()) as TasteQuizSession
}

export async function listTasteQuizKnowledge(
  direction: TasteQuizKnowledgeDirection,
  cursor?: string | null,
  limit = 20,
): Promise<TasteQuizKnowledgeListResponse> {
  const params = new URLSearchParams({ direction, limit: String(limit) })
  if (cursor != null && cursor.trim() !== '') {
    params.set('cursor', cursor.trim())
  }
  return apiJson<TasteQuizKnowledgeListResponse>(`/api/taste-quiz/knowledge?${params.toString()}`)
}

export async function batchTasteQuizKnowledge(
  ownerId: string,
  guesserUserIds: string[],
): Promise<TasteQuizKnowledgeBatchResponse> {
  return apiJson<TasteQuizKnowledgeBatchResponse>('/api/taste-quiz/knowledge/batch', {
    method: 'POST',
    body: JSON.stringify({
      owner_id: ownerId,
      guesser_user_ids: guesserUserIds,
    }),
  })
}

export async function createTasteQuizInvite(): Promise<TasteQuizCreateInviteResponse> {
  return apiJson<TasteQuizCreateInviteResponse>('/api/taste-quiz/invites', {
    method: 'POST',
    body: JSON.stringify({}),
  })
}

export async function resolveTasteQuizInvite(token: string): Promise<TasteQuizResolveInviteResponse> {
  return apiJson<TasteQuizResolveInviteResponse>(
    `/api/taste-quiz/invites/${encodeURIComponent(token.trim())}`,
  )
}
