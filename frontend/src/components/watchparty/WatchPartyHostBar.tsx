import { Button } from '@telegram-apps/telegram-ui'
import { Pause, Play } from 'lucide-react'

import { formatPlaybackMs } from '../../lib/watchPartyTime'

export type WatchPartyHostBarProps = {
  busy: boolean
  playing: boolean
  syncMs: number
  seekDraftMs: number
  seekDraftDirty: boolean
  onSeekDraftChange: (ms: number) => void
  onPlay: () => void
  onPause: () => void
  onSeek: () => void
  onEndSession: () => void
}

export function WatchPartyHostBar({
  busy,
  playing,
  syncMs,
  seekDraftMs,
  seekDraftDirty,
  onSeekDraftChange,
  onPlay,
  onPause,
  onSeek,
  onEndSession,
}: WatchPartyHostBarProps) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="text-[11px] text-(--tgui--hint_color)">
          Время комнаты для гостей
        </p>
        <p className="font-mono text-sm tabular-nums">
          {formatPlaybackMs(syncMs)}
          {' '}
          {playing ? '▶' : '⏸'}
        </p>
      </div>
      <p className="mb-2 text-[11px] text-(--tgui--hint_color)">
        Плеер сверху — отдельный. После перемотки в нём выставьте то же время ползунком и нажмите «Применить».
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <Button mode="filled" size="s" disabled={busy} onClick={onPlay} aria-label="Play">
          <Play className="block size-4" />
        </Button>
        <Button mode="gray" size="s" disabled={busy} onClick={onPause} aria-label="Pause">
          <Pause className="block size-4" />
        </Button>
        <input
          type="range"
          min={0}
          max={7_200_000}
          step={1000}
          value={seekDraftMs}
          onChange={(e) => onSeekDraftChange(Number(e.target.value))}
          className="min-w-24 flex-1"
          aria-label="Позиция для гостей"
        />
        <span className="min-w-14 font-mono text-xs tabular-nums text-(--tgui--hint_color)">
          {seekDraftDirty ? formatPlaybackMs(seekDraftMs) : '—'}
        </span>
        <Button mode="gray" size="s" disabled={busy || !seekDraftDirty} onClick={onSeek}>
          Применить
        </Button>
        <Button mode="plain" size="s" className="ml-auto!" onClick={onEndSession}>
          Завершить
        </Button>
      </div>
    </div>
  )
}
