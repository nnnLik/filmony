import { ArrowLeft, Play } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { Link, useNavigate, useParams } from 'react-router'

import { getFilmById } from '../api/cardApi'
import { ApiError, formatApiDetail } from '../api/client'
import type { Film } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'

function filmErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) {
      return 'Фильм не найден'
    }
    return formatApiDetail(error.detail)
  }
  return 'Не удалось загрузить фильм'
}

export function FilmWatchPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const { filmId: filmIdRaw } = useParams<{ filmId: string }>()
  const filmId = Number(filmIdRaw)

  const filmQuery = useQuery<Film, Error>({
    queryKey: ['film', filmId],
    enabled: auth.kind === 'ready' && Number.isFinite(filmId) && filmId > 0,
    queryFn: () => getFilmById(filmId),
    retry: false,
  })

  useEffect(() => {
    if (auth.kind === 'unauthenticated') {
      void navigate(`/login?returnTo=${encodeURIComponent(window.location.pathname)}`, { replace: true })
    }
  }, [auth.kind, navigate])

  if (auth.kind === 'loading' || auth.kind === 'error') {
    return <PageLoadingState authPending className="min-h-dvh bg-black" />
  }

  if (!Number.isFinite(filmId) || filmId <= 0) {
    return <PageErrorState message="Фильм не найден" className="min-h-dvh bg-black" />
  }

  if (filmQuery.isLoading) {
    return <PageLoadingState message="Загрузка…" className="min-h-dvh bg-black" />
  }

  if (filmQuery.isError) {
    return (
      <div className="flex min-h-dvh flex-col bg-black text-white">
        <WatchHeader filmId={filmId} title="Просмотр" />
        <PageErrorState message={filmErrorMessage(filmQuery.error)} className="flex-1 bg-black" />
      </div>
    )
  }

  const film = filmQuery.data
  if (!film) {
    return null
  }

  return (
    <div className="flex min-h-dvh flex-col bg-black text-white">
      <WatchHeader filmId={filmId} title={film.title} />
      <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-4 px-4 pb-8 pt-2">
        <div className="relative flex aspect-video w-full items-center justify-center rounded-lg bg-white/5">
          <Play className="size-12 text-white/30" />
        </div>
        <div className="flex flex-col gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-5 text-center">
          <p className="text-base font-semibold">Просмотр скоро появится</p>
          <p className="text-sm text-(--tgui--hint_color)">
            Интерфейс готов — подключим воспроизведение в одном из следующих обновлений.
          </p>
        </div>
        <label className="flex flex-col gap-1 text-sm opacity-50">
          <span className="text-(--tgui--hint_color)">Озвучка</span>
          <select className="rounded-lg border border-white/15 bg-black px-3 py-2" disabled defaultValue="">
            <option value="">Скоро</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm opacity-50">
          <span className="text-(--tgui--hint_color)">Качество</span>
          <select className="rounded-lg border border-white/15 bg-black px-3 py-2" disabled defaultValue="">
            <option value="">Скоро</option>
          </select>
        </label>
      </div>
    </div>
  )
}

function WatchHeader({ filmId, title }: { filmId: number; title: string }) {
  return (
    <header className="flex items-center gap-3 px-4 py-3">
      <Link
        to={`/films/${filmId}`}
        className="inline-flex items-center gap-1 text-sm text-white/80 no-underline"
      >
        <ArrowLeft className="size-4" />
        Назад
      </Link>
      <h1 className="truncate text-base font-semibold">{title}</h1>
    </header>
  )
}
