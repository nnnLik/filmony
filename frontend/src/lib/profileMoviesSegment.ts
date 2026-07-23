export type ProfileMoviesSegment = 'rated' | 'watchlist'

export const PROFILE_MOVIES_SEGMENT_PARAM = 'movies'

export function profileMoviesSegmentFromSearchParams(
  searchParams: URLSearchParams,
): ProfileMoviesSegment {
  return searchParams.get(PROFILE_MOVIES_SEGMENT_PARAM) === 'watchlist' ? 'watchlist' : 'rated'
}

export function applyProfileMoviesSegmentToSearchParams(
  searchParams: URLSearchParams,
  segment: ProfileMoviesSegment,
): URLSearchParams {
  const next = new URLSearchParams(searchParams)
  if (segment === 'watchlist') {
    next.set(PROFILE_MOVIES_SEGMENT_PARAM, 'watchlist')
  } else {
    next.delete(PROFILE_MOVIES_SEGMENT_PARAM)
  }
  return next
}
