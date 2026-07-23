import { act, render, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { useProfileMoviesSegmentFromUrl } from '../useProfileMoviesSegmentFromUrl'

function ProfileSegmentHarness({
  onChange,
}: {
  onChange: (value: ReturnType<typeof useProfileMoviesSegmentFromUrl>) => void
}) {
  const value = useProfileMoviesSegmentFromUrl()
  onChange(value)
  return null
}

function SearchProbe({ onChange }: { onChange: (search: string) => void }) {
  const location = useLocation()
  onChange(location.search)
  return null
}

describe('useProfileMoviesSegmentFromUrl', () => {
  it('hydrates watchlist segment from the url on mount', () => {
    let latest: ReturnType<typeof useProfileMoviesSegmentFromUrl> | null = null

    render(
      <MemoryRouter initialEntries={['/profile?movies=watchlist']}>
        <Routes>
          <Route
            path="/profile"
            element={
              <ProfileSegmentHarness
                onChange={(value) => {
                  latest = value
                }}
              />
            }
          />
        </Routes>
      </MemoryRouter>,
    )

    expect(latest?.[0]).toBe('watchlist')
  })

  it('writes segment changes back to the url', async () => {
    let latest: ReturnType<typeof useProfileMoviesSegmentFromUrl> | null = null
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
              <ProfileSegmentHarness
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
      latest?.[1]('watchlist')
    })

    await waitFor(() => {
      expect(new URLSearchParams(latestSearch).get('movies')).toBe('watchlist')
    })
  })

  it('returns to watchlist segment after navigating back from a card', async () => {
    let latest: ReturnType<typeof useProfileMoviesSegmentFromUrl> | null = null
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
      <MemoryRouter initialEntries={['/profile?movies=watchlist', '/cards/1']} initialIndex={1}>
        <SearchProbe
          onChange={(search) => {
            latestSearch = search
          }}
        />
        <Routes>
          <Route
            path="/profile"
            element={
              <ProfileSegmentHarness
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
      expect(new URLSearchParams(latestSearch).get('movies')).toBe('watchlist')
    })

    expect(latest?.[0]).toBe('watchlist')
  })
})
