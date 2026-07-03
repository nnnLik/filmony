import { act, render, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { DEFAULT_RATED_CARDS_QUERY } from '../../lib/ratedCardsListQuery'
import { useRatedCardsQueryFromUrl } from '../useRatedCardsQueryFromUrl'

function ProfileFiltersHarness({
  onChange,
}: {
  onChange: (value: ReturnType<typeof useRatedCardsQueryFromUrl>) => void
}) {
  const value = useRatedCardsQueryFromUrl()
  onChange(value)
  return null
}

function SearchProbe({ onChange }: { onChange: (search: string) => void }) {
  const location = useLocation()
  onChange(location.search)
  return null
}

describe('useRatedCardsQueryFromUrl', () => {
  it('hydrates profile filters from the url on mount', () => {
    let latest: ReturnType<typeof useRatedCardsQueryFromUrl> | null = null

    render(
      <MemoryRouter initialEntries={['/profile?filmTitle=thriller&sort=rating_desc']}>
        <Routes>
          <Route
            path="/profile"
            element={
              <ProfileFiltersHarness
                onChange={(value) => {
                  latest = value
                }}
              />
            }
          />
        </Routes>
      </MemoryRouter>,
    )

    expect(latest?.[0]).toEqual({
      ...DEFAULT_RATED_CARDS_QUERY,
      filmTitle: 'thriller',
      sort: 'rating_desc',
    })
  })

  it('writes filter changes back to the url', async () => {
    let latest: ReturnType<typeof useRatedCardsQueryFromUrl> | null = null
    let latestSearch = ''

    render(
      <MemoryRouter initialEntries={['/profile']}>
        <SearchProbe
          onChange={(search) => {
            latestSearch = search
          }}
        />
        <Routes>
          <Route
            path="/profile"
            element={
              <ProfileFiltersHarness
                onChange={(value) => {
                  latest = value
                }}
              />
            }
          />
        </Routes>
      </MemoryRouter>,
    )

    act(() => {
      latest?.[1]({
        ...DEFAULT_RATED_CARDS_QUERY,
        filmTitle: 'matrix',
        sort: 'rating_asc',
      })
    })

    await waitFor(() => {
      const params = new URLSearchParams(latestSearch)
      expect(params.get('filmTitle')).toBe('matrix')
      expect(params.get('sort')).toBe('rating_asc')
    })
  })

  it('restores filters from the url after remount', () => {
    let latest: ReturnType<typeof useRatedCardsQueryFromUrl> | null = null

    const view = render(
      <MemoryRouter initialEntries={['/profile?filmTitle=thriller&sort=rating_desc']}>
        <Routes>
          <Route
            path="/profile"
            element={
              <ProfileFiltersHarness
                onChange={(value) => {
                  latest = value
                }}
              />
            }
          />
        </Routes>
      </MemoryRouter>,
    )

    view.unmount()

    render(
      <MemoryRouter initialEntries={['/profile?filmTitle=thriller&sort=rating_desc']}>
        <Routes>
          <Route
            path="/profile"
            element={
              <ProfileFiltersHarness
                onChange={(value) => {
                  latest = value
                }}
              />
            }
          />
        </Routes>
      </MemoryRouter>,
    )

    expect(latest).not.toBeNull()
    const [restoredQuery] = latest!
    expect(restoredQuery.filmTitle).toBe('thriller')
    expect(restoredQuery.sort).toBe('rating_desc')
  })
})

describe('profile card return navigation', () => {
  it('returns to the same profile url with filters intact', async () => {
    let latest: ReturnType<typeof useRatedCardsQueryFromUrl> | null = null
    let latestSearch = ''

    function CardPage() {
      const navigate = useNavigate()
      return (
        <button type="button" onClick={() => { void navigate(-1) }}>
          back
        </button>
      )
    }

    render(
      <MemoryRouter initialEntries={['/profile?filmTitle=thriller', '/cards/1']} initialIndex={1}>
        <SearchProbe
          onChange={(search) => {
            latestSearch = search
          }}
        />
        <Routes>
          <Route
            path="/profile"
            element={
              <ProfileFiltersHarness
                onChange={(value) => {
                  latest = value
                }}
              />
            }
          />
          <Route path="/cards/:cardId" element={<CardPage />} />
        </Routes>
      </MemoryRouter>,
    )

    act(() => {
      document.querySelector('button')?.click()
    })

    await waitFor(() => {
      expect(latestSearch).toBe('?filmTitle=thriller')
    })

    expect(latest).not.toBeNull()
    expect(latest![0].filmTitle).toBe('thriller')
  })
})
