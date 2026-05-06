import type { ReactionCatalogItem, ReactionSummary } from './profileTypes'

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

export async function getReactionCatalog(): Promise<{ items: ReactionCatalogItem[] }> {
  return apiJson<{ items: ReactionCatalogItem[] }>('/api/reactions/catalog')
}

export async function setUserReaction(body: UserReactionSetBody): Promise<UserReactionSetResponse> {
  return apiJson<UserReactionSetResponse>('/api/reactions', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}
