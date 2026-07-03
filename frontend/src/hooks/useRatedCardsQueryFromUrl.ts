import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import {
  type RatedCardsListQuery,
  mergeRatedCardsFilterSearchParams,
  ratedCardsQueryFromSearchParams,
  ratedCardsQueryKey,
  ratedCardsQueryToSearchParams,
} from '../lib/ratedCardsListQuery'

/** Keeps profile rated-cards filters in sync with URL search params. */
export function useRatedCardsQueryFromUrl(): [RatedCardsListQuery, (next: RatedCardsListQuery) => void] {
  const location = useLocation()
  const navigate = useNavigate()
  const [ratedQuery, setRatedQuery] = useState<RatedCardsListQuery>(() =>
    ratedCardsQueryFromSearchParams(new URLSearchParams(location.search)),
  )

  useEffect(() => {
    const fromUrl = ratedCardsQueryFromSearchParams(new URLSearchParams(location.search))
    queueMicrotask(() => {
      setRatedQuery((prev) => {
        if (ratedCardsQueryKey(prev) === ratedCardsQueryKey(fromUrl)) {
          return prev
        }
        return fromUrl
      })
    })
  }, [location.search])

  useEffect(() => {
    const currentParams = new URLSearchParams(location.search)
    const filterParams = ratedCardsQueryToSearchParams(ratedQuery)
    const merged = mergeRatedCardsFilterSearchParams(currentParams, filterParams)
    const next = merged.toString()
    const current = currentParams.toString()
    if (next === current) {
      return
    }

    void navigate(
      {
        pathname: location.pathname,
        search: next === '' ? '' : `?${next}`,
      },
      { replace: true },
    )
  }, [ratedQuery, navigate, location.pathname, location.search])

  return [ratedQuery, setRatedQuery]
}
