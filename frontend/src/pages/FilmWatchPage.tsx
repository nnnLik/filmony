import { ArrowLeft } from 'lucide-react'
import { Button } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { useCallback, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router'

import { getFilmPlayback, type FilmPlaybackResponse } from '../api/filmPlaybackApi'
import { ApiError, formatApiDetail } from '../api/client'
import { useAuthStatus } from '../auth/useAuthStatus'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { openExternalUrl } from '../lib/openExternalUrl'

function playbackErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) {
      return 'Фильм не найден'
    }
    if (error.status === 422 || error.detail === 'playback_unavailable') {
      return 'Смотреть недоступно для этого фильма'
    }
    if (error.status >= 500) {
      return 'Не удалось загрузить плеер. Попробуйте позже'
    }
    return formatApiDetail(error.detail)
  }
  return 'Не удалось загрузить плеер. Попробуйте позже'
}

export function FilmWatchPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const { filmId: filmIdRaw } = useParams<{ filmId: string }>()
  const filmId = Number(filmIdRaw)

  const playbackQuery = useQuery<FilmPlaybackResponse, Error>({
    queryKey: ['film-playback', filmId],
    enabled: auth.kind === 'ready' && Number.isFinite(filmId) && filmId > 0,
    queryFn: () => getFilmPlayback(filmId),
    retry: false,
  })

  useEffect(() => {
    if (auth.kind === 'unauthenticated') {
      void navigate(`/login?returnTo=${encodeURIComponent(window.location.pathname)}`, { replace: true })
    }
  }, [auth.kind, navigate])

  const handleBack = useCallback(() => {
    const state: unknown = window.history.state
    let historyIdx: number | null = null
    if (typeof state === 'object' && state !== null && 'idx' in state) {
      const rawIdx = Reflect.get(state, 'idx')
      if (typeof rawIdx === 'number') {
        historyIdx = rawIdx
      }
    }
    if (historyIdx != null && historyIdx > 0) {
      void navigate(-1)
      return
    }
    void navigate(`/films/${filmId}`, { replace: true })
  }, [filmId, navigate])

  if (auth.kind === 'loading' || auth.kind === 'error') {
    return <PageLoadingState authPending className="min-h-dvh bg-black" />
  }

  if (!Number.isFinite(filmId) || filmId <= 0) {
    return <PageErrorState message="Фильм не найден" className="min-h-dvh bg-black" />
  }

  if (playbackQuery.isLoading) {
    return <PageLoadingState message="Загрузка плеера…" className="min-h-dvh bg-black" />
  }

  if (playbackQuery.isError) {
    return (
      <div className="flex min-h-dvh flex-col bg-black text-white">
        <WatchHeader title="Просмотр" onBack={handleBack} />
        <PageErrorState message={playbackErrorMessage(playbackQuery.error)} className="flex-1 bg-black" />
      </div>
    )
  }

  const playback = playbackQuery.data
  if (!playback) {
    return null
  }

  return (
    <div className="flex min-h-dvh flex-col bg-black text-white">
      <WatchHeader title={playback.title} onBack={handleBack} />
      <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-4 px-4 pb-8 pt-2">
        <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-black">
          <iframe
            title={`Просмотр: ${playback.title}`}
            src={playback.iframe_url}
            className="absolute inset-0 size-full border-0"
            allow="autoplay; fullscreen; encrypted-media; picture-in-picture"
            allowFullScreen
            referrerPolicy="no-referrer-when-downgrade"
          />
        </div>
        <Button
          mode="gray"
          stretched
          onClick={() => {
            openExternalUrl(playback.iframe_url)
          }}
        >
          Открыть в браузере
        </Button>
        <p className="text-center text-xs text-(--tgui--hint_color)">
          Если плеер не загрузился в Telegram, откройте просмотр во внешнем браузере.
        </p>
      </div>
    </div>
  )
}

function WatchHeader({ title, onBack }: { title: string; onBack: () => void }) {
  return (
    <header className="flex items-center gap-3 px-4 py-3">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-1 text-sm text-white/80"
      >
        <ArrowLeft className="size-4" />
        Назад
      </button>
      <h1 className="truncate text-base font-semibold">{title}</h1>
    </header>
  )
}
