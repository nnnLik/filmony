import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import {
  applyProfileMoviesSegmentToSearchParams,
  profileMoviesSegmentFromSearchParams,
  type ProfileMoviesSegment,
} from '../lib/profileMoviesSegment'

/** Keeps profile movies segment (rated vs «Позже») in sync with URL search params. */
export function useProfileMoviesSegmentFromUrl(): [ProfileMoviesSegment, (next: ProfileMoviesSegment) => void] {
  const location = useLocation()
  const navigate = useNavigate()
  const [moviesSegment, setMoviesSegment] = useState<ProfileMoviesSegment>(() => {
    const fromUrl = profileMoviesSegmentFromSearchParams(new URLSearchParams(location.search))
    if (fromUrl === 'watchlist') {
      return 'watchlist'
    }
    const fromState = (location.state as { moviesSegment?: string } | null)?.moviesSegment
    return fromState === 'watchlist' ? 'watchlist' : 'rated'
  })

  useEffect(() => {
    const fromUrl = profileMoviesSegmentFromSearchParams(new URLSearchParams(location.search))
    queueMicrotask(() => {
      setMoviesSegment((prev) => (prev === fromUrl ? prev : fromUrl))
    })
  }, [location.search])

  useEffect(() => {
    const currentParams = new URLSearchParams(location.search)
    const merged = applyProfileMoviesSegmentToSearchParams(currentParams, moviesSegment)
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
  }, [moviesSegment, navigate, location.pathname, location.search])

  return [moviesSegment, setMoviesSegment]
}
