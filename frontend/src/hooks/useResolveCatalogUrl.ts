import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import {
  isLikelyUrl,
  resolveCatalogByUrl,
  type CatalogResolveByUrlResponse,
} from '../api/catalogApi'

export type UseResolveCatalogUrlOptions = {
  enabled?: boolean
}

/** Immediate catalog resolve when input looks like a URL (no debounce). */
export function useResolveCatalogUrl(input: string, options?: UseResolveCatalogUrlOptions) {
  const trimmed = useMemo(() => input.trim(), [input])
  const urlLike = isLikelyUrl(input)

  return useQuery<CatalogResolveByUrlResponse, Error>({
    queryKey: ['catalogResolveByUrl', trimmed],
    queryFn: () => resolveCatalogByUrl(trimmed),
    enabled: (options?.enabled ?? true) && urlLike && trimmed !== '',
    retry: false,
  })
}
