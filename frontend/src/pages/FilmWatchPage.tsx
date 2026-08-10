import { Button } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router'

import { getFilmPlayback, type FilmPlaybackResponse } from '../api/filmPlaybackApi'
import {
  bridgeWatchPartyToWatchSession,
  endWatchParty,
  leaveWatchParty,
  postWatchPartyPlayback,
  sendWatchPartyHeartbeat,
} from '../api/watchPartyApi'
import { ApiError, formatApiDetail } from '../api/client'
import type {
  WatchPartyMember,
  WatchPartyMessage,
  WatchPartyPlaybackState,
  WatchPartySnapshot,
  WatchPartySseEvent,
} from '../api/watchPartyTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import {
  WATCH_PARTY_TYPING_DISPLAY_MS,
} from '../components/watchparty/WatchPartyChatSheet'
import { WatchPartyEndSheet } from '../components/watchparty/WatchPartyEndSheet'
import { WatchPartyHeader } from '../components/watchparty/WatchPartyHeader'
import { WatchPartyHostBar } from '../components/watchparty/WatchPartyHostBar'
import { WatchPartyInlineChat } from '../components/watchparty/WatchPartyInlineChat'
import { WatchPartyInviteSheet } from '../components/watchparty/WatchPartyInviteSheet'
import { WatchPartyMemberStrip } from '../components/watchparty/WatchPartyMemberStrip'
import { WatchPartyRosterSheet } from '../components/watchparty/WatchPartyRosterSheet'
import { useEnsureWatchParty } from '../hooks/useEnsureWatchParty'
import { useWatchPartyEvents } from '../hooks/useWatchPartyEvents'
import { useWatchingNowOfUsers } from '../hooks/useWatchingNowOfUsers'
import { mergeWatchPartyMessages } from '../lib/mergeWatchPartyMessages'
import { expectedPlaybackMs, formatPlaybackMs } from '../lib/watchPartyTime'

const DRIFT_THRESHOLD_MS = 8000
const DRIFT_CHECK_INTERVAL_MS = 5000
const HEARTBEAT_INTERVAL_MS = 30_000

function parseSnapshotPayload(payload: Record<string, unknown>): Partial<WatchPartySnapshot> | null {
  const playbackRaw = payload.playback_state
  const membersRaw = payload.members
  if (typeof playbackRaw !== 'object' || playbackRaw === null) {
    return null
  }
  const members = Array.isArray(membersRaw) ? (membersRaw as WatchPartyMember[]) : []
  return {
    playback_state: playbackRaw as WatchPartyPlaybackState,
    members,
  }
}

function parseWatchPartyMessages(raw: unknown): WatchPartyMessage[] {
  if (!Array.isArray(raw)) {
    return []
  }
  const out: WatchPartyMessage[] = []
  for (const item of raw) {
    if (typeof item !== 'object' || item === null) {
      continue
    }
    const record = item as Record<string, unknown>
    const id = record.id
    const authorUserId = record.author_user_id
    const body = record.body
    const createdAt = record.created_at
    if (
      typeof id === 'number'
      && typeof authorUserId === 'string'
      && typeof body === 'string'
      && typeof createdAt === 'string'
    ) {
      out.push({
        id,
        author_user_id: authorUserId,
        body,
        created_at: createdAt,
      })
    }
  }
  return out
}

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
  const [searchParams] = useSearchParams()
  const { filmId: filmIdRaw } = useParams<{ filmId: string }>()
  const filmId = Number(filmIdRaw)
  const partySlug = searchParams.get('party')

  const [messages, setMessages] = useState<WatchPartyMessage[]>([])
  const [chatOpen, setChatOpen] = useState(false)
  const [rosterOpen, setRosterOpen] = useState(false)
  const [inviteOpen, setInviteOpen] = useState(false)
  const [endSheetOpen, setEndSheetOpen] = useState(false)
  const [endBusy, setEndBusy] = useState(false)
  const [syncHintOpen, setSyncHintOpen] = useState(false)
  const [driftSeconds, setDriftSeconds] = useState<number | null>(null)
  const [hostPositionMs, setHostPositionMs] = useState(0)
  const [playbackBusy, setPlaybackBusy] = useState(false)
  const [guestAnchorMs, setGuestAnchorMs] = useState<number | null>(null)
  const [guestAnchorAt, setGuestAnchorAt] = useState<number | null>(null)
  const [typingByUserId, setTypingByUserId] = useState<Map<string, { name: string; expiresAt: number }>>(
    () => new Map(),
  )
  const [typingNowMs, setTypingNowMs] = useState(() => Date.now())
  const guestAnchoredRef = useRef(false)

  const snapshotRef = useRef<WatchPartySnapshot | null>(null)

  const playbackQuery = useQuery<FilmPlaybackResponse, Error>({
    queryKey: ['film-playback', filmId],
    enabled: auth.kind === 'ready' && Number.isFinite(filmId) && filmId > 0,
    queryFn: () => getFilmPlayback(filmId),
    retry: false,
  })

  const {
    snapshot,
    setSnapshot,
    loading: partyLoading,
    error: partyError,
  } = useEnsureWatchParty(filmId, partySlug, auth.kind === 'ready')

  useEffect(() => {
    snapshotRef.current = snapshot
  }, [snapshot])

  useEffect(() => {
    if (snapshot == null) {
      return
    }
    queueMicrotask(() => {
      setHostPositionMs(snapshot.playback_state.position_ms)
      if (!guestAnchoredRef.current) {
        guestAnchoredRef.current = true
        setGuestAnchorMs(snapshot.playback_state.position_ms)
        setGuestAnchorAt(Date.now())
      }
    })
  }, [snapshot])

  const partyId = snapshot?.id ?? null
  const isHost = snapshot?.viewer_role === 'host'
  const isGuest = snapshot?.viewer_role === 'guest'

  const handleSseEvent = useCallback((event: WatchPartySseEvent) => {
    if (event.type === 'party_ended') {
      const film = snapshotRef.current?.film_id
      if (film) {
        void navigate(`/films/${film}`, { replace: true })
      }
      return
    }
    if (event.type === 'playback_state') {
      const raw = event.payload.playback_state
      if (typeof raw === 'object' && raw !== null) {
        setSnapshot((prev) => (prev ? { ...prev, playback_state: raw as WatchPartyPlaybackState } : prev))
      }
      return
    }
    if (event.type === 'chat_message') {
      const raw = event.payload.message
      if (typeof raw === 'object' && raw !== null) {
        const msg = raw as WatchPartyMessage
        setMessages((prev) => mergeWatchPartyMessages(prev, [msg]))
      }
      return
    }
    if (event.type === 'chat_message_deleted') {
      const id = event.payload.message_id
      if (typeof id === 'number') {
        setMessages((prev) => prev.filter((m) => m.id !== id))
      }
      return
    }
    if (event.type === 'typing') {
      const userId = event.payload.user_id
      const displayName = event.payload.display_name
      if (typeof userId === 'string' && typeof displayName === 'string') {
        setTypingByUserId((prev) => {
          const next = new Map(prev)
          next.set(userId, {
            name: displayName,
            expiresAt: Date.now() + WATCH_PARTY_TYPING_DISPLAY_MS,
          })
          return next
        })
      }
      return
    }
    if (event.type === 'snapshot') {
      const partial = parseSnapshotPayload(event.payload)
      if (partial?.playback_state) {
        setSnapshot((prev) => (prev ? { ...prev, ...partial, playback_state: partial.playback_state! } : prev))
      }
      if (partial && 'members' in partial && partial.members) {
        setSnapshot((prev) => (prev ? { ...prev, members: partial.members! } : prev))
      }
      if (event.payload.messages) {
        const parsed = parseWatchPartyMessages(event.payload.messages)
        if (parsed.length > 0) {
          setMessages((prev) => mergeWatchPartyMessages(prev, parsed))
        }
      }
      return
    }
    if (event.type === 'presence' && Array.isArray(event.payload.members)) {
      setSnapshot((prev) => (prev ? { ...prev, members: event.payload.members as WatchPartyMember[] } : prev))
    }
  }, [navigate, setSnapshot])

  useWatchPartyEvents(partyId, auth.kind === 'ready' && partyId != null, handleSseEvent)

  useEffect(() => {
    if (auth.kind === 'unauthenticated') {
      void navigate(`/login?returnTo=${encodeURIComponent(window.location.pathname + window.location.search)}`, {
        replace: true,
      })
    }
  }, [auth.kind, navigate])

  useEffect(() => {
    if (partyId == null || auth.kind !== 'ready') {
      return undefined
    }
    const tick = () => {
      void sendWatchPartyHeartbeat(partyId).catch(() => undefined)
    }
    tick()
    const id = window.setInterval(tick, HEARTBEAT_INTERVAL_MS)
    return () => {
      window.clearInterval(id)
    }
  }, [partyId, auth.kind])

  useEffect(() => {
    const id = window.setInterval(() => {
      const now = Date.now()
      setTypingNowMs(now)
      setTypingByUserId((prev) => {
        let changed = false
        const next = new Map<string, { name: string; expiresAt: number }>()
        for (const [userId, entry] of prev) {
          if (entry.expiresAt > now) {
            next.set(userId, entry)
          } else {
            changed = true
          }
        }
        return changed ? next : prev
      })
    }, 1000)
    return () => window.clearInterval(id)
  }, [])

  const guestExpectedMs = snapshot?.playback_state
    ? expectedPlaybackMs(snapshot.playback_state)
    : 0

  useEffect(() => {
    if (!isGuest || snapshot?.playback_state == null) {
      queueMicrotask(() => setDriftSeconds(null))
      return undefined
    }

    const check = () => {
      const state = snapshotRef.current?.playback_state
      if (state == null) {
        return
      }
      const hostMs = expectedPlaybackMs(state)
      const anchorMs = guestAnchorMs ?? hostMs
      const anchorAt = guestAnchorAt ?? Date.now()
      const guestEstimatedMs = anchorMs + (state.playing ? Math.max(0, Date.now() - anchorAt) : 0)
      const driftMs = Math.abs(hostMs - guestEstimatedMs)
      if (!state.playing || driftMs > DRIFT_THRESHOLD_MS) {
        setDriftSeconds(Math.max(1, Math.round(driftMs / 1000)))
      } else {
        setDriftSeconds(null)
      }
    }

    check()
    const id = window.setInterval(check, DRIFT_CHECK_INTERVAL_MS)
    return () => window.clearInterval(id)
  }, [guestAnchorAt, guestAnchorMs, isGuest, snapshot?.playback_state])

  const activeMembers = useMemo(
    () => snapshot?.members.filter((m) => m.status === 'active' || m.status === 'away') ?? [],
    [snapshot?.members],
  )

  const rosterUserIds = useMemo(
    () => snapshot?.members.map((m) => m.user_id) ?? [],
    [snapshot?.members],
  )
  const { watchingByUserId } = useWatchingNowOfUsers(rosterUserIds, {
    enabled: rosterOpen && rosterUserIds.length > 0,
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

  const typingNames = useMemo(() => {
    const viewerId = auth.kind === 'ready' ? readMyProfileBundleCache()?.profile.id ?? null : null
    const names: string[] = []
    for (const [userId, entry] of typingByUserId) {
      if (viewerId != null && userId === viewerId) {
        continue
      }
      if (entry.expiresAt > typingNowMs) {
        names.push(entry.name)
      }
    }
    return names
  }, [auth, typingByUserId, typingNowMs])

  const handleBack = useCallback(async () => {
    if (partyId != null) {
      try {
        await leaveWatchParty(partyId)
      } catch {
        /* ignore */
      }
    }
    void navigate(`/films/${filmId}`, { replace: true })
  }, [filmId, navigate, partyId])

  const sendPlayback = useCallback(
    async (action: 'play' | 'pause' | 'seek', positionMs?: number) => {
      if (partyId == null) {
        return
      }
      setPlaybackBusy(true)
      try {
        const state = await postWatchPartyPlayback(partyId, {
          action,
          position_ms: positionMs,
        })
        setSnapshot((prev) => (prev ? { ...prev, playback_state: state } : prev))
      } finally {
        setPlaybackBusy(false)
      }
    },
    [partyId, setSnapshot],
  )

  const handleEndOnly = useCallback(async () => {
    if (partyId == null) {
      return
    }
    setEndBusy(true)
    try {
      await endWatchParty(partyId)
      void navigate(`/films/${filmId}`, { replace: true })
    } finally {
      setEndBusy(false)
      setEndSheetOpen(false)
    }
  }, [filmId, navigate, partyId])

  const handleEndAndBridge = useCallback(async () => {
    if (partyId == null) {
      return
    }
    setEndBusy(true)
    try {
      const result = await bridgeWatchPartyToWatchSession(partyId)
      void navigate(`/films/${filmId}`, {
        replace: true,
        state: { watchSessionId: result.watch_session_id },
      })
    } catch {
      await handleEndOnly()
    } finally {
      setEndBusy(false)
      setEndSheetOpen(false)
    }
  }, [filmId, handleEndOnly, navigate, partyId])

  const handleSync = useCallback(() => {
    if (snapshot?.playback_state == null) {
      return
    }
    const ms = expectedPlaybackMs(snapshot.playback_state)
    setGuestAnchorMs(ms)
    setGuestAnchorAt(Date.now())
    setSyncHintOpen(true)
    setDriftSeconds(null)
  }, [snapshot])

  const iframeUrl = snapshot?.playback_iframe_url ?? playbackQuery.data?.iframe_url ?? ''
  const title = snapshot?.film_title ?? playbackQuery.data?.title ?? 'Просмотр'

  if (auth.kind === 'loading' || auth.kind === 'error') {
    return <PageLoadingState authPending className="min-h-dvh bg-black" />
  }

  if (!Number.isFinite(filmId) || filmId <= 0) {
    return <PageErrorState message="Фильм не найден" className="min-h-dvh bg-black" />
  }

  if (playbackQuery.isLoading || partyLoading) {
    return <PageLoadingState message="Загрузка плеера…" className="min-h-dvh bg-black" />
  }

  if (playbackQuery.isError) {
    return (
      <div className="flex min-h-dvh flex-col bg-black text-white">
        <WatchPartyHeader
          title="Просмотр"
          memberCount={1}
          onBack={() => void navigate(`/films/${filmId}`, { replace: true })}
          onMemberCountTap={() => undefined}
          onChat={() => undefined}
        />
        <PageErrorState message={playbackErrorMessage(playbackQuery.error)} className="flex-1 bg-black" />
      </div>
    )
  }

  if (partyError != null || snapshot == null) {
    return <PageErrorState message={partyError ?? 'Не удалось подключиться к просмотру'} className="min-h-dvh bg-black" />
  }

  return (
    <div className="flex min-h-dvh flex-col bg-black text-white">
      <WatchPartyHeader
        title={title}
        memberCount={activeMembers.length}
        onBack={() => void handleBack()}
        onMemberCountTap={() => setRosterOpen(true)}
        onChat={() => setChatOpen((v) => !v)}
        onInvite={isHost ? () => setInviteOpen(true) : undefined}
      />

      <WatchPartyMemberStrip
        members={snapshot.members}
        onTap={() => setRosterOpen(true)}
      />

      <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-2 px-3 pb-3 pt-1">
        <div className="relative aspect-video w-full shrink-0 overflow-hidden rounded-lg bg-black">
          <iframe
            title={`Просмотр: ${title}`}
            src={iframeUrl}
            className="absolute inset-0 size-full border-0"
            allow="autoplay; fullscreen; encrypted-media; picture-in-picture"
            allowFullScreen
            referrerPolicy="no-referrer-when-downgrade"
          />
          {syncHintOpen ? (
            <div className="absolute inset-x-4 bottom-4 rounded-lg bg-black/85 p-3 text-sm">
              <p className="mb-2">
                Перемотайте плеер на
                {' '}
                <strong>{formatPlaybackMs(guestExpectedMs)}</strong>
                {' '}
                и нажмите play.
              </p>
              <Button mode="gray" size="s" onClick={() => setSyncHintOpen(false)}>
                Понятно
              </Button>
            </div>
          ) : null}
        </div>

        {isGuest && driftSeconds != null ? (
          <div className="flex items-center justify-between gap-2 rounded-lg border border-amber-400/40 bg-amber-400/10 px-3 py-2 text-sm">
            <span>
              Отстали на ~
              {driftSeconds}
              {' '}
              сек
            </span>
            <Button mode="filled" size="s" onClick={handleSync}>
              Синхронизироваться
            </Button>
          </div>
        ) : null}

        {isHost ? (
          <WatchPartyHostBar
            busy={playbackBusy}
            playing={snapshot.playback_state.playing}
            positionMs={hostPositionMs}
            onPositionChange={setHostPositionMs}
            onPlay={() => void sendPlayback('play', hostPositionMs)}
            onPause={() => void sendPlayback('pause', hostPositionMs)}
            onSeek={() => void sendPlayback('seek', hostPositionMs)}
            onEndSession={() => setEndSheetOpen(true)}
          />
        ) : null}
      </div>

      {chatOpen ? (
        <WatchPartyInlineChat
          partyId={snapshot.id}
          messages={messages}
          onMessagesChange={setMessages}
          typingNames={typingNames}
          onClose={() => setChatOpen(false)}
        />
      ) : null}

      <WatchPartyRosterSheet
        open={rosterOpen}
        members={snapshot.members}
        watchingByUserId={watchingByUserId}
        onClose={() => setRosterOpen(false)}
      />

      <WatchPartyInviteSheet
        open={inviteOpen}
        partyId={snapshot.id}
        onClose={() => setInviteOpen(false)}
      />

      <WatchPartyEndSheet
        open={endSheetOpen}
        busy={endBusy}
        onClose={() => setEndSheetOpen(false)}
        onEndOnly={() => void handleEndOnly()}
        onEndAndRateTogether={() => void handleEndAndBridge()}
      />
    </div>
  )
}
