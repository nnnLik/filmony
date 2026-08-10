import { Button } from '@telegram-apps/telegram-ui'
import { Pause, Play } from 'lucide-react'

import { formatPlaybackMs } from '../../lib/watchPartyTime'

export type WatchPartyHostBarProps = {
  busy: boolean
  playing: boolean
  positionMs: number
  onPositionChange: (ms: number) => void
  onPlay: () => void
  onPause: () => void
  onSeek: () => void
  onEndSession: () => void
}

export function WatchPartyHostBar({
  busy,
  playing,
  positionMs,
  onPositionChange,
  onPlay,
  onPause,
  onSeek,
  onEndSession,
}: WatchPartyHostBarProps) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">
      <p className="mb-2 text-[11px] text-(--tgui--hint_color)">
        Синхронизация для гостей. Свой плеер — в iframe выше.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <Button mode="filled" size="s" disabled={busy} onClick={onPlay} aria-label="Play">
          <Play className="block size-4" />
        </Button>
        <Button mode="gray" size="s" disabled={busy} onClick={onPause} aria-label="Pause">
          <Pause className="block size-4" />
        </Button>
        <span className="min-w-14 font-mono text-xs tabular-nums">{formatPlaybackMs(positionMs)}</span>
        <input
          type="range"
          min={0}
          max={7_200_000}
          step={1000}
          value={positionMs}
          onChange={(e) => onPositionChange(Number(e.target.value))}
          className="min-w-24 flex-1"
          aria-label="Позиция воспроизведения"
        />
        <Button mode="gray" size="s" disabled={busy} onClick={onSeek}>
          Seek
        </Button>
        <Button mode="plain" size="s" className="ml-auto!" onClick={onEndSession}>
          Завершить
        </Button>
      </div>
      <p className="mt-1 text-[11px] text-(--tgui--hint_color)">
        {playing ? '▶ играет' : '⏸ пауза'}
      </p>
    </div>
  )
}
