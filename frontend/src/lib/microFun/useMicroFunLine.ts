import { useMemo } from 'react'

import type { MicroFunPoolKey } from './microFunCopy'
import { resolveMicroFunLine } from './resolveMicroFunLine'
import { utcDateBucket } from './pickMicroFunLine'

export function useMicroFunLine(
  poolKey: MicroFunPoolKey,
  fallback: string,
  userId: string | number | null | undefined,
): string {
  const dateBucket = utcDateBucket()
  return useMemo(
    () =>
      resolveMicroFunLine({
        poolKey,
        fallback,
        userId,
        dateBucket,
      }),
    [poolKey, fallback, userId, dateBucket],
  )
}
