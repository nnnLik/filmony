import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'

import {
  isLikelyUrl,
  searchCatalogCandidates,
  type CatalogCandidatesResponse,
} from '../api/catalogApi'
import { normalizeCatalogSearchQuery } from '../lib/normalizeCatalogSearchQuery'

const CATALOG_CANDIDATES_DEBOUNCE_MS = 800

export type UseCatalogCandidatesOptions = {
  enabled?: boolean
  page?: number
  limit?: number
}

/** Debounced mixed catalog search; skips URL-like input and queries shorter than 3 chars. */
export function useCatalogCandidates(q: string, options?: UseCatalogCandidatesOptions) {
  const normalized = useMemo(() => normalizeCatalogSearchQuery(q), [q])
  const urlLike = isLikelyUrl(q)
  const [debouncedQ, setDebouncedQ] = useState('')

  useEffect(() => {
    if (urlLike || normalized.length < 3) {
      const timer = window.setTimeout(() => setDebouncedQ(''))
      return () => window.clearTimeout(timer)
    }
    const timer = window.setTimeout(
      () => setDebouncedQ(normalized),
      CATALOG_CANDIDATES_DEBOUNCE_MS,
    )
    return () => window.clearTimeout(timer)
  }, [normalized, urlLike])

  const enabled =
    (options?.enabled ?? true) && !urlLike && debouncedQ.length >= 3

  return useQuery<CatalogCandidatesResponse, Error>({
    queryKey: ['catalogCandidates', debouncedQ, options?.page ?? 1, options?.limit ?? 15],
    queryFn: ({ signal }) =>
      searchCatalogCandidates({
        q: debouncedQ,
        page: options?.page,
        limit: options?.limit,
        signal,
      }),
    enabled,
  })
}
