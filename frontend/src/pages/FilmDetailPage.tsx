import { Button, Section, Title } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { getFilmById } from '../api/cardApi'
import { ApiError, formatApiDetail } from '../api/client'
import { deleteMyWatchlistFilm, getMyWatchlistFilmPresence, postMyWatchlistFilm } from '../api/profileApi'
import type { Film } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { clearMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { safeHapticSuccess } from '../lib/safeHaptic'

export function FilmDetailPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const { filmId: filmIdRaw } = useParams<{ filmId: string }>()
  const parsedId = Number(filmIdRaw)
  const filmId = Number.isInteger(parsedId) && parsedId >= 1 ? parsedId : 0

  const [film, setFilm] = useState<Film | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inWatchlist, setInWatchlist] = useState<boolean | null>(null)
  const [removeBusy, setRemoveBusy] = useState(false)
  const [addWatchlistBusy, setAddWatchlistBusy] = useState(false)
  const [watchlistActionErr, setWatchlistActionErr] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    void (async () => {
      await Promise.resolve()
      if (!alive) return
      setWatchlistActionErr(null)
      if (filmId < 1) {
        setError('Некорректный id в каталоге')
        setLoading(false)
        setFilm(null)
        return
      }
      setLoading(true)
      setError(null)
      try {
        const f = await getFilmById(filmId)
        if (!alive) return
        setFilm(f)
      } catch (e) {
        if (!alive) return
        if (e instanceof ApiError && e.status === 404) {
          setError('Запись в каталоге не найдена.')
        } else if (e instanceof ApiError) {
          setError(formatApiDetail(e.detail))
        } else {
          setError('Не удалось загрузить запись каталога')
        }
        setFilm(null)
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [filmId])

  useEffect(() => {
    let alive = true
    void (async () => {
      if (auth.kind !== 'ready' || filmId < 1) {
        queueMicrotask(() => {
          if (auth.kind !== 'ready') setInWatchlist(null)
        })
        return
      }
      try {
        const m = await getMyWatchlistFilmPresence(filmId)
        if (!alive) return
        setInWatchlist(m.in_watchlist)
      } catch {
        if (!alive) return
        setInWatchlist(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind, filmId])

  const onAddToWatchlist = useCallback(async () => {
    if (filmId < 1 || film == null) return
    setAddWatchlistBusy(true)
    setWatchlistActionErr(null)
    try {
      await postMyWatchlistFilm(film.id)
      setInWatchlist(true)
      clearMyProfileBundleCache()
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) {
        if (e.status === 409) {
          setWatchlistActionErr('Уже в списке «к просмотру».')
          setInWatchlist(true)
          return
        }
        const msg = formatApiDetail(e.detail).toLowerCase()
        if (msg.includes('movie card already exists')) {
          setWatchlistActionErr('У вас уже есть оценённая карточка для этого тайтла.')
          return
        }
        setWatchlistActionErr(formatApiDetail(e.detail))
      } else {
        setWatchlistActionErr('Не удалось добавить в список')
      }
    } finally {
      setAddWatchlistBusy(false)
    }
  }, [film, filmId])

  const onRemoveFromWatchlist = useCallback(async () => {
    if (filmId < 1) return
    setRemoveBusy(true)
    setWatchlistActionErr(null)
    try {
      await deleteMyWatchlistFilm(filmId)
      setInWatchlist(false)
      clearMyProfileBundleCache()
    } catch (e) {
      if (e instanceof ApiError) {
        setWatchlistActionErr(formatApiDetail(e.detail))
      } else {
        setWatchlistActionErr('Не удалось убрать из списка')
      }
    } finally {
      setRemoveBusy(false)
    }
  }, [filmId])

  if (auth.kind === 'loading' || auth.kind === 'skipped') {
    return (
      <div className="min-h-dvh bg-(--tgui--bg_color) px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Вход…</p>
      </div>
    )
  }

  if (auth.kind === 'error') {
    return (
      <div className="min-h-dvh bg-(--tgui--bg_color) px-4 py-12">
        <p className="filmony-text-panel text-sm text-(--tgui--destructive_text_color)">{auth.message}</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) pb-8 text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <button
          type="button"
          className="flex min-h-10 min-w-10 items-center justify-center rounded-lg text-lg text-(--tgui--link_color)"
          aria-label="Назад"
          onClick={() => {
            void navigate(-1)
          }}
        >
          ←
        </button>
        <span className="truncate text-sm font-medium text-(--tgui--hint_color)">Каталог</span>
      </header>

      <main className="mx-auto max-w-md px-4 pt-4">
        {loading ? (
          <p className="filmony-text-panel py-12 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
        ) : null}
        {!loading && error != null ? (
          <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-4 py-4">
            <p className="text-sm text-(--tgui--hint_color)">{error}</p>
            <Button className="mt-4" stretched onClick={() => void navigate('/')}>
              На главную
            </Button>
          </div>
        ) : null}
        {!loading && error == null && film != null ? (
          <Section header={film.title}>
            <div className="px-3 py-3">
              <div className="filmony-text-panel flex gap-3">
                <div className="h-40 w-28 shrink-0 overflow-hidden rounded-xl bg-(--tgui--secondary_bg_color)">
                  {film.poster_url ? (
                    <img src={film.poster_url} alt={film.title} className="h-full w-full object-cover" />
                  ) : null}
                </div>
                <div className="min-w-0">
                  <Title level="3" weight="2">
                    {film.title}
                  </Title>
                  <p className="mt-1 text-sm text-(--tgui--hint_color)">{film.year ?? 'Год неизвестен'}</p>
                  {film.genres.length > 0 ? (
                    <p className="mt-2 text-xs text-(--tgui--hint_color)">{film.genres.join(' · ')}</p>
                  ) : null}
                </div>
              </div>

              {auth.kind === 'ready' ? (
                <div className="mt-6 flex flex-col gap-2">
                  <Link to={`/cards/new?filmId=${encodeURIComponent(String(film.id))}`} className="no-underline">
                    <Button stretched>Оценить просмотр</Button>
                  </Link>
                  {inWatchlist === false ? (
                    <Button
                      mode="gray"
                      stretched
                      disabled={addWatchlistBusy}
                      onClick={() => void onAddToWatchlist()}
                    >
                      {addWatchlistBusy ? 'Добавляем…' : 'К просмотру'}
                    </Button>
                  ) : null}
                  {inWatchlist === true ? (
                    <Button
                      mode="gray"
                      stretched
                      disabled={removeBusy}
                      onClick={() => void onRemoveFromWatchlist()}
                    >
                      {removeBusy ? 'Убираем…' : 'Убрать из списка «к просмотру»'}
                    </Button>
                  ) : null}
                  {watchlistActionErr != null ? (
                    <p className="text-sm text-(--tgui--destructive_text_color)">{watchlistActionErr}</p>
                  ) : null}
                </div>
              ) : null}
            </div>
          </Section>
        ) : null}
      </main>
    </div>
  )
}
