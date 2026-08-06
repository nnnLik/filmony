import type { UserCollectionProgress } from '../api/collectionsTypes'

export function collectionProgressPercent(
  progress: UserCollectionProgress | null | undefined,
): number | null {
  if (progress == null || progress.total_count <= 0) {
    return null
  }
  return Math.min(100, Math.round((progress.rated_count / progress.total_count) * 100))
}
