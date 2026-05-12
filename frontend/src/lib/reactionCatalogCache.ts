import { getReactionCatalog } from '../api/reactionApi'
import type { ReactionGroupedCatalog } from '../api/profileTypes'

/** Кэш каталога реакций на клиенте (снижает повторные запросы при скролле ленты). */
export const REACTION_CATALOG_TTL_MS = 5 * 60 * 1000

let inflight: Promise<ReactionGroupedCatalog> | null = null
let cached: { at: number; data: ReactionGroupedCatalog } | null = null

export function clearReactionCatalogCache(): void {
  inflight = null
  cached = null
}

export async function loadReactionCatalog(): Promise<ReactionGroupedCatalog> {
  const now = Date.now()
  if (cached != null && now - cached.at < REACTION_CATALOG_TTL_MS) {
    return cached.data
  }
  if (!inflight) {
    inflight = getReactionCatalog()
      .then((r) => {
        cached = { at: Date.now(), data: r }
        return r
      })
      .catch((err) => {
        inflight = null
        throw err
      })
  }
  return inflight
}
