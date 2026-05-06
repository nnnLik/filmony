import type {
  ReactionActorsResponse,
  ReactionGroupedCatalog,
  ReactionSummary,
} from './profileTypes'

import { apiJson } from './client'

export type UserReactionSetBody = {
  target_kind: 'movie_card' | 'movie_card_comment'
  target_id: number
  reaction_type_id: number
}

export type UserReactionSetResponse = {
  target_kind: string
  target_id: number
  reactions: ReactionSummary
}

export async function getReactionCatalog(): Promise<ReactionGroupedCatalog> {
  return apiJson<ReactionGroupedCatalog>('/api/reactions/catalog')
}

export async function getReactionActors(params: {
  target_kind: 'movie_card' | 'movie_card_comment'
  target_id: number
  reaction_type_id: number
  limit?: number
}): Promise<ReactionActorsResponse> {
  const sp = new URLSearchParams({
    target_kind: params.target_kind,
    target_id: String(params.target_id),
    reaction_type_id: String(params.reaction_type_id),
  })
  if (params.limit != null) sp.set('limit', String(params.limit))
  return apiJson<ReactionActorsResponse>(`/api/reactions/actors?${sp.toString()}`)
}

export async function setUserReaction(body: UserReactionSetBody): Promise<UserReactionSetResponse> {
  return apiJson<UserReactionSetResponse>('/api/reactions', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}
