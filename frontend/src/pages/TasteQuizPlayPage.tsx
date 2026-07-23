import { Button } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'

import { ApiError, formatApiDetail } from '../api/client'
import {
  abandonTasteQuizSession,
  createTasteQuizSession,
  submitTasteQuizAnswer,
} from '../api/tasteQuizApi'
import type { TasteQuizPairProgress, TasteQuizSession, TasteQuizSessionCard } from '../api/tasteQuizTypes'
import { getPublicProfileById, subscribeToUser } from '../api/profileApi'
import type { PublicProfile } from '../api/profileTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { TasteQuizFollowSoftBanner } from '../components/tasteQuiz/TasteQuizFollowSoftBanner'
import { TasteQuizGateScreen } from '../components/tasteQuiz/TasteQuizGateScreen'
import { TasteQuizGuessScreen } from '../components/tasteQuiz/TasteQuizGuessScreen'
import { TasteQuizRevealScreen } from '../components/tasteQuiz/TasteQuizRevealScreen'
import { TasteQuizSummaryScreen } from '../components/tasteQuiz/TasteQuizSummaryScreen'
import { displayNameFromProfile } from '../lib/profileDisplay'
import { normalizeRating } from '../lib/createCardBinding'
import { safeHapticSuccess } from '../lib/safeHaptic'
import {
  tasteQuizCanPlayQueryKey,
  tasteQuizSessionQueryKey,
} from '../lib/tasteQuizQueryKeys'
import { useTasteQuizCanPlay } from '../hooks/useTasteQuizCanPlay'
import { useTasteQuizSession } from '../hooks/useTasteQuizSession'

type PlayPhase = 'loading' | 'gate' | 'follow' | 'resume' | 'guess' | 'reveal' | 'summary'

function currentCard(session: TasteQuizSession): TasteQuizSessionCard | null {
  if (session.status === 'completed') {
    return null
  }
  const idx = session.current_index
  return session.cards[idx] ?? null
}

function derivePhase(
  session: TasteQuizSession | null,
  localRevealCard: TasteQuizSessionCard | null,
): PlayPhase {
  if (localRevealCard != null) {
    return 'reveal'
  }
  if (session == null) {
    return 'loading'
  }
  if (session.status === 'completed') {
    return 'summary'
  }
  if (currentCard(session) != null) {
    return 'guess'
  }
  return 'summary'
}

export function TasteQuizPlayPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { ownerId: ownerIdParam } = useParams<{ ownerId?: string }>()
  const [searchParams] = useSearchParams()
  const inviteToken = searchParams.get('invite')?.trim() || null

  const ownerId = useMemo(() => decodeURIComponent(ownerIdParam ?? '').trim(), [ownerIdParam])

  const [ownerProfile, setOwnerProfile] = useState<PublicProfile | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [session, setSession] = useState<TasteQuizSession | null>(null)
  const [phase, setPhase] = useState<PlayPhase>('loading')
  const [revealCard, setRevealCard] = useState<TasteQuizSessionCard | null>(null)
  const [pairProgress, setPairProgress] = useState<TasteQuizPairProgress | null>(null)
  const [rating, setRating] = useState(7)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [followBusy, setFollowBusy] = useState(false)
  const [resumeSessionId, setResumeSessionId] = useState<string | null>(null)

  const canPlayQuery = useTasteQuizCanPlay(ownerId, inviteToken, {
    enabled: auth.kind === 'ready' && ownerId !== '',
  })

  const sessionQuery = useTasteQuizSession(sessionId, {
    enabled: auth.kind === 'ready' && sessionId != null,
  })

  useEffect(() => {
    if (auth.kind !== 'ready' || ownerId === '') return
    let alive = true
    void (async () => {
      try {
        const p = await getPublicProfileById(ownerId)
        if (!alive) return
        setOwnerProfile(p)
      } catch {
        if (!alive) return
        setError('Профиль не найден')
      }
    })()
    return () => {
      alive = false
    }
  }, [auth.kind, ownerId])

  const startSession = useCallback(async () => {
    if (ownerId === '') return
    setBusy(true)
    setError(null)
    try {
      const created = await createTasteQuizSession(ownerId, inviteToken)
      setSessionId(created.id)
      setSession(created)
      setPhase(derivePhase(created, null))
      void queryClient.invalidateQueries({ queryKey: tasteQuizCanPlayQueryKey(ownerId, inviteToken) })
    } catch (e: unknown) {
      if (e instanceof ApiError && e.status === 409) {
        const detail = e.detail
        if (typeof detail === 'object' && detail != null && 'session_id' in detail) {
          const rawSid = (detail as Record<string, unknown>).session_id
          const sid = typeof rawSid === 'string' ? rawSid : null
          if (sid != null) {
            setResumeSessionId(sid)
            setPhase('resume')
            return
          }
        }
      }
      setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось начать игру')
    } finally {
      setBusy(false)
    }
  }, [ownerId, inviteToken, queryClient])

  useEffect(() => {
    if (canPlayQuery.isLoading || canPlayQuery.data == null || sessionId != null) {
      return
    }
    const data = canPlayQuery.data
    queueMicrotask(() => {
      if (data.reason === 'owner_insufficient_cards') {
        setPhase('gate')
        return
      }
      if (!data.can_play && data.reason === 'not_following') {
        setPhase('follow')
        return
      }
      if (!data.can_play && data.reason === 'active_session_exists' && data.active_session_id != null) {
        setPhase('resume')
        setResumeSessionId(data.active_session_id)
        return
      }
      if (data.can_play) {
        void startSession()
      }
    })
  }, [canPlayQuery.data, canPlayQuery.isLoading, sessionId, startSession])

  useEffect(() => {
    if (sessionQuery.data == null) return
    queueMicrotask(() => {
      setSession(sessionQuery.data)
      if (revealCard == null) {
        setPhase(derivePhase(sessionQuery.data, null))
      }
    })
  }, [sessionQuery.data, revealCard])

  const ownerName = ownerProfile != null ? displayNameFromProfile(ownerProfile) : 'пользователя'

  async function resumeSession() {
    if (resumeSessionId == null) return
    setSessionId(resumeSessionId)
    setPhase('loading')
    await queryClient.invalidateQueries({ queryKey: tasteQuizSessionQueryKey(resumeSessionId) })
  }

  async function abandonAndRestart() {
    if (resumeSessionId == null) return
    setBusy(true)
    setError(null)
    try {
      await abandonTasteQuizSession(resumeSessionId)
      setSessionId(null)
      setSession(null)
      setResumeSessionId(null)
      setRevealCard(null)
      void queryClient.invalidateQueries({ queryKey: tasteQuizCanPlayQueryKey(ownerId, inviteToken) })
      await startSession()
    } catch (e: unknown) {
      setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось отменить сессию')
    } finally {
      setBusy(false)
    }
  }

  async function submitGuess() {
    if (session == null) return
    const card = currentCard(session)
    if (card == null) return
    setBusy(true)
    setError(null)
    try {
      const outcome = await submitTasteQuizAnswer(session.id, card.session_card_id, rating)
      safeHapticSuccess()
      setSession(outcome.session)
      setPairProgress(outcome.pair_progress)
      setRevealCard(outcome.card)
      setPhase('reveal')
      void queryClient.setQueryData(tasteQuizSessionQueryKey(session.id), outcome.session)
    } catch (e: unknown) {
      setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось отправить ответ')
    } finally {
      setBusy(false)
    }
  }

  function continueFromReveal() {
    if (session == null) return
    setRevealCard(null)
    if (session.status === 'completed') {
      setPhase('summary')
      return
    }
    setRating(normalizeRating(7))
    setPhase('guess')
  }

  async function abandonCurrent() {
    if (session == null) return
    const confirmed = window.confirm('Выйти из игры? Ответы сохранятся, незавершённая карточка — нет.')
    if (!confirmed) return
    setBusy(true)
    try {
      await abandonTasteQuizSession(session.id)
      void navigate(-1)
    } catch (e: unknown) {
      setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось выйти')
    } finally {
      setBusy(false)
    }
  }

  async function followOwner() {
    if (ownerId === '') return
    setFollowBusy(true)
    try {
      await subscribeToUser(ownerId)
      void queryClient.invalidateQueries({ queryKey: tasteQuizCanPlayQueryKey(ownerId, inviteToken) })
      setPhase('loading')
    } catch (e: unknown) {
      setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось подписаться')
    } finally {
      setFollowBusy(false)
    }
  }

  if (auth.kind === 'loading' || auth.kind === 'error' || auth.kind === 'skipped') {
    return (
      <div className="px-4 py-16 text-center text-sm text-(--tgui--hint_color)">
        <p className="filmony-text-panel inline-block">Загрузка…</p>
      </div>
    )
  }

  if (ownerId === '') {
    return (
      <div className="mx-auto max-w-md px-4 py-12 text-center">
        <p className="text-sm text-(--tgui--destructive_text_color)">Некорректный профиль</p>
        <Link className="mt-4 inline-block text-sm text-(--tgui--link_color)" to="/">
          На главную
        </Link>
      </div>
    )
  }

  const activeCard = session != null ? currentCard(session) : null
  const progressCurrent = session != null ? Math.min(session.current_index + 1, session.card_count) : 0
  const guesserFollowsOwner = canPlayQuery.data?.guesser_follows_owner ?? false

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-2 py-2 backdrop-blur-md">
        <button
          type="button"
          className="flex min-h-10 min-w-10 items-center justify-center rounded-xl text-lg text-(--tgui--link_color)"
          aria-label="Назад"
          onClick={() => void navigate(-1)}
        >
          ←
        </button>
        <h1 className="min-w-0 flex-1 truncate text-base font-semibold tracking-tight">
          Угадать вкус · {ownerName}
        </h1>
      </header>

      {inviteToken != null && ownerProfile != null ? (
        <div className="mx-auto max-w-md px-4 pt-4">
          <TasteQuizFollowSoftBanner
            ownerName={ownerName}
            ownerUserId={ownerProfile.id}
            following={guesserFollowsOwner}
            followBusy={followBusy}
            onFollow={() => void followOwner()}
          />
        </div>
      ) : null}

      {error != null ? (
        <p className="filmony-text-panel mx-auto max-w-md px-4 pt-4 text-center text-sm text-(--tgui--destructive_text_color)">
          {error}
        </p>
      ) : null}

      {phase === 'gate' && canPlayQuery.data != null ? (
        <TasteQuizGateScreen
          ownerName={ownerName}
          ownerRatedCount={canPlayQuery.data.owner_rated_count}
          gateMinRatedCards={canPlayQuery.data.gate_min_rated_cards}
          onBack={() => void navigate(-1)}
        />
      ) : null}

      {phase === 'follow' ? (
        <div className="mx-auto flex max-w-md flex-col items-center px-4 py-12 text-center">
          <p className="filmony-text-panel text-sm leading-relaxed text-(--tgui--hint_color)">
            Подпишитесь на {ownerName}, чтобы угадывать его вкус.
          </p>
          <Button className="mt-6 max-w-xs" stretched disabled={followBusy} onClick={() => void followOwner()}>
            {followBusy ? '…' : 'Подписаться'}
          </Button>
        </div>
      ) : null}

      {phase === 'resume' ? (
        <div className="mx-auto flex max-w-md flex-col items-center px-4 py-12 text-center">
          <p className="filmony-text-panel text-sm leading-relaxed text-(--tgui--text_color)">
            У вас уже есть незаконченная игра с {ownerName}.
          </p>
          <div className="mt-6 flex w-full max-w-xs flex-col gap-2">
            <Button stretched disabled={busy} onClick={() => void resumeSession()}>
              Продолжить игру
            </Button>
            <Button mode="gray" stretched disabled={busy} onClick={() => void abandonAndRestart()}>
              Начать заново
            </Button>
          </div>
        </div>
      ) : null}

      {(phase === 'loading' || (phase === 'guess' && activeCard == null && session == null)) ? (
        <p className="filmony-text-panel py-16 text-center text-sm text-(--tgui--hint_color)">
          {busy ? 'Запуск…' : 'Загрузка…'}
        </p>
      ) : null}

      {phase === 'guess' && activeCard != null && session != null ? (
        <TasteQuizGuessScreen
          card={activeCard}
          progressCurrent={progressCurrent}
          progressTotal={session.card_count}
          rating={rating}
          onRatingChange={setRating}
          submitBusy={busy}
          onSubmit={() => void submitGuess()}
          onAbandon={() => void abandonCurrent()}
        />
      ) : null}

      {phase === 'reveal' && revealCard != null ? (
        <TasteQuizRevealScreen card={revealCard} onContinue={continueFromReveal} />
      ) : null}

      {phase === 'summary' && session != null ? (
        <TasteQuizSummaryScreen
          session={session}
          pairProgress={pairProgress}
          ownerName={ownerName}
          ownerUserId={ownerId}
          playAgainDisabled
        />
      ) : null}
    </div>
  )
}
