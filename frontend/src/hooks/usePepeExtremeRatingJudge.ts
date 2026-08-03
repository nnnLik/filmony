import { useCallback, useEffect, useRef, useState } from 'react'

import type { MicroFunPoolKey } from '../lib/microFun/microFunCopy'
import { getMicroFunPool } from '../lib/microFun/microFunCopy'
import { pickMicroFunLine } from '../lib/microFun/pickMicroFunLine'

const LOW_THRESHOLD = 1
const HIGH_THRESHOLD = 10

function poolForRating(rating: number): MicroFunPoolKey | null {
  if (rating === LOW_THRESHOLD) {
    return 'extreme_rating_low'
  }
  if (rating === HIGH_THRESHOLD) {
    return 'extreme_rating_high'
  }
  return null
}

function pickExtremeLine(poolKey: MicroFunPoolKey, userId: string | number | null | undefined, nonce: number): string {
  const pool = getMicroFunPool(poolKey)
  const userPart = userId != null && String(userId).trim() !== '' ? String(userId).trim() : 'anon'
  return (
    pickMicroFunLine({
      pool,
      seedParts: [poolKey, userPart, String(nonce)],
    }) ?? pool[0] ?? ''
  )
}

export type UsePepeExtremeRatingJudgeResult = {
  message: string | null
  dismiss: () => void
}

/**
 * Shows a Pepe line when rating crosses exactly 1 or 10 (not on every tick while staying there).
 */
export function usePepeExtremeRatingJudge(
  rating: number,
  userId: string | number | null | undefined,
): UsePepeExtremeRatingJudgeResult {
  const [message, setMessage] = useState<string | null>(null)
  const prevRatingRef = useRef<number | null>(null)
  const crossingNonceRef = useRef(0)

  useEffect(() => {
    const prev = prevRatingRef.current
    prevRatingRef.current = rating

    if (prev == null) {
      return
    }

    const poolKey = poolForRating(rating)
    if (poolKey == null || prev === rating) {
      return
    }

    crossingNonceRef.current += 1
    setMessage(pickExtremeLine(poolKey, userId, crossingNonceRef.current))
  }, [rating, userId])

  const dismiss = useCallback(() => {
    setMessage(null)
  }, [])

  return { message, dismiss }
}
