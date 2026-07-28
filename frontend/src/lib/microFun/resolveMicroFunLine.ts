import { getMicroFunPool, type MicroFunPoolKey } from './microFunCopy'
import { buildMicroFunSeedParts, pickMicroFunLine, utcDateBucket } from './pickMicroFunLine'

export function resolveMicroFunLine({
  poolKey,
  fallback,
  userId,
  dateBucket = utcDateBucket(),
}: {
  poolKey: MicroFunPoolKey
  fallback: string
  userId: string | number | null | undefined
  dateBucket?: string
}): string {
  if (userId == null || String(userId).trim() === '') {
    return fallback
  }
  const pool = getMicroFunPool(poolKey)
  const picked = pickMicroFunLine({
    pool,
    seedParts: buildMicroFunSeedParts(poolKey, userId, dateBucket),
  })
  return picked ?? fallback
}
