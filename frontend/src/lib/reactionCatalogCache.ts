import { getReactionCatalog } from '../api/reactionApi'
import type { ReactionCatalogItem } from '../api/profileTypes'

let inflight: Promise<ReactionCatalogItem[]> | null = null

export function clearReactionCatalogCache(): void {
  inflight = null
}

export async function loadReactionCatalogItems(): Promise<ReactionCatalogItem[]> {
  if (!inflight) {
    inflight = getReactionCatalog()
      .then((r) => r.items)
      .catch((err) => {
        inflight = null
        throw err
      })
  }
  return inflight
}
