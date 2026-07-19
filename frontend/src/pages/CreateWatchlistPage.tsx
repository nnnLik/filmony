import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link, useMatch, useNavigate, useSearchParams } from 'react-router-dom'

import { getMovieCardById } from '../api/cardApi'
import { ApiError, formatApiDetail } from '../api/client'
import { getMyProfile } from '../api/profileApi'
import { useAuthStatus } from '../auth/useAuthStatus'
import {
  WatchlistForm,
  type WatchlistFormEditMode,
} from '../components/create/WatchlistForm'
import type { CardCompany } from '../api/profileTypes'
import {
  watchlistBindingFromCardId,
  watchlistBindingFromCatalogItemId,
  watchlistBindingFromFilmId,
  watchlistBindingFromMovieCard,
  type WatchlistBinding,
} from '../lib/watchlistBinding'

function CreateWatchlistShell({
  title,
  onBack,
  loading,
  error,
  children,
}: {
  title: string
  onBack: () => void
  loading: boolean
  error: string | null
  children: ReactNode
}) {
  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md">
        <div className="flex items-center justify-between px-4 pb-3 pt-3">
          <button
            type="button"
            onClick={onBack}
            className="flex h-10 w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color) active:opacity-70"
            aria-label="Назад"
          >
            ←
          </button>
          <h1 className="text-base font-semibold tracking-tight text-(--tgui--text_color)">{title}</h1>
          <span className="w-10" />
        </div>
      </header>

      <main className="space-y-4 px-4 py-6">
        {error != null ? (
          <div className="rounded-2xl border border-(--tgui--destructive_text_color) bg-[color-mix(in_srgb,var(--tgui--destructive_text_color)_10%,transparent)] px-3 py-2">
            <p className="text-sm text-(--tgui--destructive_text_color)">{error}</p>
          </div>
        ) : null}
        {loading ? (
          <p className="filmony-text-panel py-16 text-center text-sm text-(--tgui--hint_color)">
            Загружаем…
          </p>
        ) : (
          children
        )}
      </main>
    </div>
  )
}

function useEditPlannedCardId(): number | null {
  const editPlannedMatch = useMatch('/cards/:cardId/edit-planned')
  return useMemo(() => {
    const raw = editPlannedMatch?.params.cardId
    if (raw == null) return null
    const value = Number(raw)
    return Number.isInteger(value) && value > 0 ? value : null
  }, [editPlannedMatch?.params.cardId])
}

function WatchlistEntryPageContent() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const editPlannedCardId = useEditPlannedCardId()
  const isEditMode = editPlannedCardId != null

  const [binding, setBinding] = useState<WatchlistBinding | null>(null)
  const [lockBinding, setLockBinding] = useState(false)
  const [loading, setLoading] = useState(isEditMode)
  const [error, setError] = useState<string | null>(null)
  const [editMode, setEditMode] = useState<WatchlistFormEditMode | undefined>(undefined)
  const [initialCompany, setInitialCompany] = useState<CardCompany>('alone')
  const [initialShelfId, setInitialShelfId] = useState<number | null>(null)
  const [initialNote, setInitialNote] = useState('')
  const [initialWatchWithUserIds, setInitialWatchWithUserIds] = useState<string[]>([])

  useEffect(() => {
    if (auth.kind !== 'ready') return
    if (isEditMode && editPlannedCardId != null) {
      let alive = true
      void (async () => {
        setLoading(true)
        setError(null)
        try {
          const [card, me] = await Promise.all([
            getMovieCardById(editPlannedCardId),
            getMyProfile(),
          ])
          if (!alive) return
          if (card.user_id == null || card.user_id !== me.id) {
            setError('Редактировать карточку может только её владелец')
            return
          }
          if (card.is_planned !== true) {
            void navigate(`/cards/${editPlannedCardId}/edit`, { replace: true })
            return
          }
          const nextBinding = await watchlistBindingFromMovieCard(card)
          if (!alive) return
          if (nextBinding == null) {
            setError('Не удалось подготовить карточку для редактирования')
            return
          }
          const entryId = card.watchlist_entry_id
          if (typeof entryId !== 'number' || entryId < 1) {
            setError('Не удалось определить запись списка «Позже»')
            return
          }
          setBinding(nextBinding)
          setLockBinding(true)
          setEditMode({ entryId, cardId: editPlannedCardId })
          setInitialCompany(card.company)
          const shelfId = card.category?.id
          setInitialShelfId(typeof shelfId === 'number' && shelfId >= 1 ? shelfId : null)
          setInitialNote(card.watch_note ?? '')
          const partnerIds = (card.planned_watch_partners ?? [])
            .map((p) => p.id)
            .filter((id) => id.trim() !== '')
          setInitialWatchWithUserIds(partnerIds)
        } catch (e) {
          if (!alive) return
          if (e instanceof ApiError) {
            setError(formatApiDetail(e.detail))
          } else {
            setError('Не удалось загрузить карточку')
          }
        } finally {
          if (alive) setLoading(false)
        }
      })()
      return () => {
        alive = false
      }
    }

    const filmIdRaw = searchParams.get('filmId')
    const catalogItemIdRaw = searchParams.get('catalogItemId')
    const watchlistCardIdRaw = searchParams.get('watchlistCardId')

    if (filmIdRaw != null && filmIdRaw !== '') {
      const filmId = Number(filmIdRaw)
      if (!Number.isInteger(filmId) || filmId <= 0) {
        queueMicrotask(() => setError('Некорректный filmId'))
        return
      }
      let alive = true
      void (async () => {
        setLoading(true)
        setError(null)
        try {
          const item = await watchlistBindingFromFilmId(filmId)
          if (!alive) return
          setBinding(item)
          setLockBinding(true)
        } catch (e) {
          if (!alive) return
          if (e instanceof ApiError) {
            setError(formatApiDetail(e.detail))
          } else {
            setError('Не удалось загрузить данные из каталога')
          }
        } finally {
          if (alive) setLoading(false)
        }
      })()
      return () => {
        alive = false
      }
    }

    if (catalogItemIdRaw != null && catalogItemIdRaw !== '') {
      const catalogItemId = Number(catalogItemIdRaw)
      if (!Number.isInteger(catalogItemId) || catalogItemId <= 0) {
        queueMicrotask(() => setError('Некорректный catalogItemId'))
        return
      }
      queueMicrotask(() => {
        setBinding(watchlistBindingFromCatalogItemId(catalogItemId))
        setLockBinding(true)
        setLoading(false)
      })
      return
    }

    if (watchlistCardIdRaw != null && watchlistCardIdRaw.trim() !== '') {
      queueMicrotask(() => {
        setBinding(watchlistBindingFromCardId(watchlistCardIdRaw.trim()))
        setLockBinding(true)
        setLoading(false)
      })
      return
    }

    queueMicrotask(() => setLoading(false))
  }, [auth.kind, editPlannedCardId, isEditMode, navigate, searchParams])

  function handleBack() {
    if (isEditMode && editPlannedCardId != null) {
      void navigate(`/cards/${editPlannedCardId}`)
      return
    }
    void navigate(-1)
  }

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
    <CreateWatchlistShell
      title={isEditMode ? 'Редактировать «Позже»' : 'В список «Позже»'}
      onBack={handleBack}
      loading={loading}
      error={error}
    >
      <WatchlistForm
        key={
          editMode != null
            ? `edit-${editMode.cardId}`
            : binding != null
              ? `create-${JSON.stringify(binding)}`
              : 'create-empty'
        }
        binding={binding}
        onBindingChange={(next) => {
          setBinding(next)
          if (next == null) setLockBinding(false)
        }}
        lockBinding={lockBinding}
        editMode={editMode}
        initialCompany={initialCompany}
        initialShelfId={initialShelfId}
        initialNote={initialNote}
        initialWatchWithUserIds={initialWatchWithUserIds}
      />
    </CreateWatchlistShell>
  )
}

export function CreateWatchlistPage() {
  return <WatchlistEntryPageContent />
}

/** Thin route wrapper for `/cards/:cardId/edit-planned`. */
export function EditPlannedWatchlistPage() {
  return <WatchlistEntryPageContent />
}
