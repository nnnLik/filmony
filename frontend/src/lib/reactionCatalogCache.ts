import { getReactionCatalog } from '../api/reactionApi'
import type { ReactionGroupedCatalog } from '../api/profileTypes'

let inflight: Promise<ReactionGroupedCatalog> | null = null

export function clearReactionCatalogCache(): void {
  inflight = null
}

export async function loadReactionCatalog(): Promise<ReactionGroupedCatalog> {
  if (!inflight) {
    inflight = getReactionCatalog()
      .then((r) => r)
      .catch((err) => {
        inflight = null
        throw err
      })
  }
  return inflight
}
