import { Avatar } from '@telegram-apps/telegram-ui'
import { Crown } from 'lucide-react'
import { useMemo } from 'react'

import type { WatchPartyMember, WatchPartyPlaybackState } from '../../api/watchPartyTypes'
import {
  expectedPlaybackMs,
  formatPlaybackMs,
  memberDisplayPositionMs,
  memberPositionDeltaSeconds,
} from '../../lib/watchPartyTime'

export type WatchPartyRoomPanelProps = {
  members: WatchPartyMember[]
  hostUserId: string
  playbackState: WatchPartyPlaybackState
  tickMs: number
  onMemberTap?: () => void
}

function statusLabel(member: WatchPartyMember): string | null {
  if (member.status === 'away') {
    return 'отошёл'
  }
  if (member.status === 'left') {
    return 'вышел'
  }
  if (member.role === 'host') {
    return 'ведущий'
  }
  return null
}

export function WatchPartyRoomPanel({
  members,
  hostUserId,
  playbackState,
  tickMs,
  onMemberTap,
}: WatchPartyRoomPanelProps) {
  const visible = useMemo(
    () => members.filter((member) => member.status === 'active' || member.status === 'away'),
    [members],
  )

  const syncMs = useMemo(
    () => expectedPlaybackMs(playbackState, tickMs),
    [playbackState, tickMs],
  )

  if (visible.length === 0) {
    return null
  }

  return (
    <section className="rounded-xl border border-white/10 bg-white/5">
      <button
        type="button"
        onClick={onMemberTap}
        className="flex w-full items-center justify-between px-3 py-2 text-left"
        aria-label={`Участники: ${visible.length}`}
      >
        <span className="text-xs font-medium text-(--tgui--hint_color)">
          В комнате ·
          {' '}
          {visible.length}
        </span>
        <span className="font-mono text-xs tabular-nums text-(--tgui--hint_color)">
          {formatPlaybackMs(syncMs)}
          {' '}
          {playbackState.playing ? '▶' : '⏸'}
        </span>
      </button>

      <ul className="divide-y divide-white/10 border-t border-white/10">
        {visible.map((member) => {
          const displayMs = memberDisplayPositionMs(member, hostUserId, playbackState, tickMs)
          const deltaSec = memberPositionDeltaSeconds(displayMs, syncMs)
          const hint = statusLabel(member)

          return (
            <li key={member.user_id} className="flex items-center gap-2.5 px-3 py-2">
              <div className="relative shrink-0">
                <Avatar size={28} src={member.photo_url ?? undefined} />
                {member.role === 'host' ? (
                  <Crown className="absolute -right-0.5 -top-0.5 size-3 text-amber-300" strokeWidth={2.5} />
                ) : null}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm leading-tight">{member.display_name}</p>
                {hint ? (
                  <p className="text-[11px] text-(--tgui--hint_color)">{hint}</p>
                ) : null}
              </div>
              <div className="shrink-0 text-right">
                <p className="font-mono text-sm tabular-nums">
                  {displayMs != null ? formatPlaybackMs(displayMs) : '—'}
                </p>
                <p className="text-[11px] text-(--tgui--hint_color)">
                  {(member.user_id === hostUserId ? playbackState.playing : member.position_playing)
                    ? '▶'
                    : '⏸'}
                  {deltaSec != null && member.role !== 'host' && deltaSec !== 0 ? (
                    <>
                      {' '}
                      ·
                      {' '}
                      {deltaSec > 0 ? '+' : ''}
                      {deltaSec}
                      {' '}
                      сек
                    </>
                  ) : null}
                </p>
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
