/** Deterministic index from seed parts (djb2-style, SSR/test-safe). */
export function hashSeedParts(seedParts: readonly string[]): number {
  let hash = 5381
  for (const part of seedParts) {
    for (let i = 0; i < part.length; i += 1) {
      hash = (hash * 33) ^ part.charCodeAt(i)
    }
    hash = (hash * 33) ^ 124 // separator
  }
  return hash >>> 0
}

export function pickMicroFunLineIndex(poolLength: number, seedParts: readonly string[]): number {
  if (poolLength <= 0) {
    return 0
  }
  return hashSeedParts(seedParts) % poolLength
}

export function pickMicroFunLine({
  pool,
  seedParts,
}: {
  pool: readonly string[]
  seedParts: readonly string[]
}): string | null {
  if (pool.length === 0) {
    return null
  }
  const index = pickMicroFunLineIndex(pool.length, seedParts)
  return pool[index] ?? null
}

export function utcDateBucket(now: Date = new Date()): string {
  return now.toISOString().slice(0, 10)
}

export function buildMicroFunSeedParts(
  poolKey: string,
  userId: string | number | null | undefined,
  dateBucket: string = utcDateBucket(),
): readonly string[] {
  const userPart =
    userId != null && String(userId).trim() !== '' ? String(userId).trim() : 'anon'
  return [poolKey, userPart, dateBucket] as const
}
