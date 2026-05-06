import { getReactionActors } from '../api/reactionApi'
import type { ReactionActor } from '../api/profileTypes'

type Key = string

const cache = new Map<Key, { at: number; items: ReactionActor[] }>()
const TTL_MS = 45_000

function key(p: {
  targetKind: 'movie_card' | 'movie_card_comment'
  targetId: number
  reactionTypeId: number
}): Key {
  return `${p.targetKind}:${p.targetId}:${p.reactionTypeId}`
}

export function clearReactionActorsCache(): void {
  cache.clear()
}

export async function loadReactionActors(p: {
  targetKind: 'movie_card' | 'movie_card_comment'
  targetId: number
  reactionTypeId: number
}): Promise<ReactionActor[]> {
  const k = key(p)
  const hit = cache.get(k)
  const now = Date.now()
  if (hit && now - hit.at < TTL_MS) return hit.items

  const res = await getReactionActors({
    target_kind: p.targetKind,
    target_id: p.targetId,
    reaction_type_id: p.reactionTypeId,
    limit: 50,
  })
  cache.set(k, { at: now, items: res.items })
  return res.items
}
