import { Avatar, Button, IconButton, Input } from '@telegram-apps/telegram-ui'
import { ArrowLeft, Crown, Link2, MessageCircle, Pause, Play, Users, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react'
import { useNavigate, useParams } from 'react-router'

import {
  createWatchPartyMessage,
  endWatchParty,
  getWatchParty,
  joinWatchParty,
  leaveWatchParty,
  postWatchPartyPlayback,
  resolveWatchPartyBySlug,
  sendWatchPartyHeartbeat,
} from '../api/watchPartyApi'
import { ApiError } from '../api/client'
import type {
  ActivePartyConflictDetail,
  WatchPartyMember,
  WatchPartyMessage,
  WatchPartyPlaybackState,
  WatchPartySnapshot,
  WatchPartySseEvent,
} from '../api/watchPartyTypes'
import { useAuthStatus } from '../auth/useAuthStatus'
import { PageErrorState } from '../components/ui/PageErrorState'
import { PageLoadingState } from '../components/ui/PageLoadingState'
import { useWatchPartyEvents } from '../hooks/useWatchPartyEvents'
import { openExternalUrl } from '../lib/openExternalUrl'
import { expectedPlaybackMs, formatPlaybackMs } from '../lib/watchPartyTime'

function isActivePartyConflict(detail: unknown): detail is ActivePartyConflictDetail {
  return (
    typeof detail === 'object'
    && detail !== null
    && Reflect.get(detail, 'code') === 'already_in_active_party'
    && typeof Reflect.get(detail, 'invite_slug') === 'string'
  )
}

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

export function WatchPartyPage() {
  const auth = useAuthStatus()
  const navigate = useNavigate()
  const { inviteSlug } = useParams<{ inviteSlug: string }>()
  const [snapshot, setSnapshot] = useState<WatchPartySnapshot | null>(null)
  const [messages, setMessages] = useState<WatchPartyMessage[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [chatOpen, setChatOpen] = useState(false)
  const [chatDraft, setChatDraft] = useState('')
  const [syncHintOpen, setSyncHintOpen] = useState(false)
  const [countdown, setCountdown] = useState<number | null>(null)
  const [hostPositionMs, setHostPositionMs] = useState(0)
  const [playbackBusy, setPlaybackBusy] = useState(false)
  const chatEndRef = useRef<HTMLDivElement | null>(null)
  const snapshotRef = useRef(snapshot)
  useEffect(() => {
    snapshotRef.current = snapshot
  }, [snapshot])

  const partyId = snapshot?.id ?? null
  const isHost = snapshot?.viewer_role === 'host'

  const handleSseEvent = useCallback((event: WatchPartySseEvent) => {
    if (event.type === 'party_ended') {
      const filmId = snapshotRef.current?.film_id
      if (filmId) {
        void navigate(`/films/${filmId}`, { replace: true })
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
        setMessages((prev) => [...prev.filter((m) => m.id !== msg.id), msg])
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
    if (event.type === 'snapshot') {
      const partial = parseSnapshotPayload(event.payload)
      if (partial?.playback_state) {
        setSnapshot((prev) => (prev ? { ...prev, ...partial, playback_state: partial.playback_state! } : prev))
      }
      if (partial && 'members' in partial && partial.members) {
        setSnapshot((prev) => (prev ? { ...prev, members: partial.members! } : prev))
      }
      if (event.payload.messages && Array.isArray(event.payload.messages)) {
        setMessages(event.payload.messages as WatchPartyMessage[])
      }
      return
    }
    if (event.type === 'presence' && Array.isArray(event.payload.members)) {
      setSnapshot((prev) => (prev ? { ...prev, members: event.payload.members as WatchPartyMember[] } : prev))
    }
  }, [navigate])

  useWatchPartyEvents(partyId, auth.kind === 'ready' && partyId != null, handleSseEvent)

  useEffect(() => {
    if (auth.kind === 'unauthenticated') {
      void navigate(`/login?returnTo=${encodeURIComponent(window.location.pathname)}`, { replace: true })
    }
  }, [auth.kind, navigate])

  useEffect(() => {
    if (auth.kind !== 'ready' || inviteSlug == null || inviteSlug === '') {
      return
    }

    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const resolved = await resolveWatchPartyBySlug(inviteSlug)
        let snap: WatchPartySnapshot
        try {
          snap = await getWatchParty(resolved.party_id)
        } catch (err) {
          if (err instanceof ApiError && err.status === 403) {
            try {
              await joinWatchParty(resolved.party_id)
            } catch (joinErr) {
              if (joinErr instanceof ApiError && joinErr.status === 409 && isActivePartyConflict(joinErr.detail)) {
                void navigate(`/watch-party/${joinErr.detail.invite_slug}`, { replace: true })
                return
              }
              throw joinErr
            }
            snap = await getWatchParty(resolved.party_id)
          } else {
            throw err
          }
        }
        if (!cancelled) {
          setSnapshot(snap)
          setHostPositionMs(snap.playback_state.position_ms)
          setMessages([])
        }
      } catch {
        if (!cancelled) {
          setError('Не удалось открыть комнату')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [auth.kind, inviteSlug, navigate])

  useEffect(() => {
    if (partyId == null || auth.kind !== 'ready') {
      return undefined
    }
    const tick = () => {
      void sendWatchPartyHeartbeat(partyId).catch(() => undefined)
    }
    tick()
    const id = window.setInterval(tick, 30_000)
    return () => {
      window.clearInterval(id)
    }
  }, [partyId, auth.kind])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, chatOpen])

  const activeMembers = useMemo(
    () => snapshot?.members.filter((m) => m.status === 'active' || m.status === 'away') ?? [],
    [snapshot?.members],
  )

  const guestExpectedMs = snapshot?.playback_state
    ? expectedPlaybackMs(snapshot.playback_state)
    : 0

  const handleShare = useCallback(async () => {
    const inviteUrl = snapshotRef.current?.invite_url
    if (!inviteUrl) {
      return
    }
    try {
      await navigator.clipboard.writeText(inviteUrl)
    } catch {
      /* clipboard unavailable */
    }
  }, [])

  const handleLeave = useCallback(async () => {
    if (partyId == null) {
      return
    }
    try {
      await leaveWatchParty(partyId)
    } catch {
      /* ignore */
    }
    const filmId = snapshotRef.current?.film_id
    if (filmId) {
      void navigate(`/films/${filmId}`, { replace: true })
    }
  }, [navigate, partyId])

  const handleEnd = useCallback(async () => {
    if (partyId == null) {
      return
    }
    await endWatchParty(partyId)
    const filmId = snapshotRef.current?.film_id
    if (filmId) {
      void navigate(`/films/${filmId}`, { replace: true })
    }
  }, [navigate, partyId])

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
    [partyId],
  )

  const startCountdown = useCallback(() => {
    let remaining = 3
    setCountdown(remaining)
    const tick = () => {
      remaining -= 1
      if (remaining <= 0) {
        setCountdown(null)
        void sendPlayback('play', hostPositionMs)
        return
      }
      setCountdown(remaining)
      window.setTimeout(tick, 1000)
    }
    window.setTimeout(tick, 1000)
  }, [hostPositionMs, sendPlayback])

  const submitChat = useCallback(async () => {
    if (partyId == null || chatDraft.trim() === '') {
      return
    }
    const body = chatDraft.trim()
    setChatDraft('')
    try {
      const msg = await createWatchPartyMessage(partyId, body)
      setMessages((prev) => [...prev, msg])
    } catch {
      setChatDraft(body)
    }
  }, [chatDraft, partyId])

  if (auth.kind === 'loading' || auth.kind === 'error') {
    return <PageLoadingState authPending className="min-h-dvh bg-black" />
  }

  if (loading) {
    return <PageLoadingState message="Подключаемся к комнате…" className="min-h-dvh bg-black" />
  }

  if (error != null || snapshot == null) {
    return <PageErrorState message={error ?? 'Комната не найдена'} className="min-h-dvh bg-black" />
  }

  return (
    <div className="flex min-h-dvh flex-col bg-black text-white">
      <header className="flex items-center gap-2 border-b border-white/10 px-3 py-2">
        <IconButton mode="gray" size="s" onClick={() => void handleLeave()} aria-label="Назад">
          <ArrowLeft className="block size-5" strokeWidth={2} />
        </IconButton>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold">{snapshot.film_title}</p>
          <p className="flex items-center gap-1 text-xs text-(--tgui--hint_color)">
            <Users className="size-3.5" />
            {activeMembers.length}
          </p>
        </div>
        <IconButton mode="gray" size="s" onClick={() => void handleShare()} aria-label="Пригласить">
          <Link2 className="block size-5" strokeWidth={2} />
        </IconButton>
        <IconButton mode="gray" size="s" onClick={() => setChatOpen((v) => !v)} aria-label="Чат">
          <MessageCircle className="block size-5" strokeWidth={2} />
        </IconButton>
      </header>

      <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-3 px-3 py-3">
        <div className="flex gap-2 overflow-x-auto pb-1">
          {snapshot.members.map((member) => (
            <div key={member.user_id} className="flex shrink-0 flex-col items-center gap-1">
              <div className="relative">
                <Avatar size={36} src={member.photo_url ?? undefined} />
                {member.role === 'host' ? (
                  <Crown className="absolute -right-1 -top-1 size-3.5 text-amber-300" />
                ) : null}
              </div>
              <span className="max-w-14 truncate text-[10px] text-(--tgui--hint_color)">
                {member.display_name}
              </span>
            </div>
          ))}
        </div>

        <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-black">
          <iframe
            title={`Смотрим вместе: ${snapshot.film_title}`}
            src={snapshot.playback_iframe_url}
            className="absolute inset-0 size-full border-0"
            allow="autoplay; fullscreen; encrypted-media; picture-in-picture"
            allowFullScreen
            referrerPolicy="no-referrer-when-downgrade"
          />
          {countdown != null ? (
            <div className="absolute inset-0 flex items-center justify-center bg-black/70 text-5xl font-bold">
              {countdown}
            </div>
          ) : null}
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

        {isHost ? (
          <div className="flex flex-col gap-2 rounded-lg border border-white/10 p-3">
            <input
              type="range"
              min={0}
              max={7_200_000}
              step={1000}
              value={hostPositionMs}
              onChange={(e) => setHostPositionMs(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex items-center justify-between text-xs text-(--tgui--hint_color)">
              <span>{formatPlaybackMs(hostPositionMs)}</span>
              <span>{snapshot.playback_state.playing ? '▶' : '⏸'}</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                mode="filled"
                size="s"
                disabled={playbackBusy}
                onClick={() => void sendPlayback('play', hostPositionMs)}
              >
                <Play className="mr-1 inline size-4" />
                Play
              </Button>
              <Button
                mode="gray"
                size="s"
                disabled={playbackBusy}
                onClick={() => void sendPlayback('pause', hostPositionMs)}
              >
                <Pause className="mr-1 inline size-4" />
                Pause
              </Button>
              <Button
                mode="gray"
                size="s"
                disabled={playbackBusy}
                onClick={() => void sendPlayback('seek', hostPositionMs)}
              >
                Seek
              </Button>
              <Button mode="bezeled" size="s" onClick={startCountdown}>
                Старт 3-2-1
              </Button>
              <Button mode="plain" size="s" onClick={() => void handleEnd()}>
                Завершить сеанс
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-2 rounded-lg border border-white/10 p-3">
            <p className="text-sm">
              Ведущий:
              {' '}
              {snapshot.playback_state.playing ? '▶' : '⏸'}
              {' '}
              {formatPlaybackMs(guestExpectedMs)}
            </p>
            <Button mode="filled" size="s" onClick={() => setSyncHintOpen(true)}>
              Синхронизироваться
            </Button>
            <Button mode="plain" size="s" onClick={() => void handleLeave()}>
              Выйти
            </Button>
          </div>
        )}

        <Button
          mode="gray"
          stretched
          onClick={() => {
            openExternalUrl(snapshot.playback_iframe_url)
          }}
        >
          Открыть в браузере
        </Button>
      </div>

      {chatOpen ? (
        <div className="fixed inset-x-0 bottom-0 z-40 max-h-[55dvh] rounded-t-2xl border border-white/10 bg-(--tgui--bg_color) p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-sm font-semibold">Чат</p>
            <IconButton mode="gray" size="s" onClick={() => setChatOpen(false)} aria-label="Закрыть чат">
              <X className="block size-5" />
            </IconButton>
          </div>
          <div className="mb-2 max-h-[32dvh] space-y-2 overflow-y-auto">
            {messages.map((message) => (
              <div key={message.id} className="rounded-lg bg-white/5 px-2 py-1.5 text-sm">
                {message.body}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              void submitChat()
            }}
          >
            <Input
              header="Сообщение"
              placeholder="Напишите в чат…"
              value={chatDraft}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setChatDraft(e.target.value)}
            />
            <Button mode="filled" type="submit">
              →
            </Button>
          </form>
        </div>
      ) : null}
    </div>
  )
}
