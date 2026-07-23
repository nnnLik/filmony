import { describe, expect, it } from 'vitest'

import {
  applyProfileMoviesSegmentToSearchParams,
  profileMoviesSegmentFromSearchParams,
} from '../profileMoviesSegment'

describe('profileMoviesSegment url helpers', () => {
  it('defaults to rated when param is missing', () => {
    expect(profileMoviesSegmentFromSearchParams(new URLSearchParams())).toBe('rated')
  })

  it('reads watchlist segment from url', () => {
    const params = new URLSearchParams('movies=watchlist')
    expect(profileMoviesSegmentFromSearchParams(params)).toBe('watchlist')
  })

  it('writes watchlist segment to url and omits rated default', () => {
    const watchlist = applyProfileMoviesSegmentToSearchParams(
      new URLSearchParams('filmTitle=matrix'),
      'watchlist',
    )
    expect(watchlist.get('movies')).toBe('watchlist')
    expect(watchlist.get('filmTitle')).toBe('matrix')

    const rated = applyProfileMoviesSegmentToSearchParams(watchlist, 'rated')
    expect(rated.get('movies')).toBeNull()
    expect(rated.get('filmTitle')).toBe('matrix')
  })
})
