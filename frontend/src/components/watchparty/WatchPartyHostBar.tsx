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
        Кнопки синхронизируют гостей. Свой pleer — в iframe выше.
      </p>
      <input
        type="range"
        min={0}
        max={7_200_000}
        step={1000}
        value={positionMs}
        onChange={(e) => onPositionChange(Number(e.target.value))}
        className="mb-1 w-full"
        aria-label="Позиция воспроизведения"
      />
      <div className="mb-2 flex items-center justify-between text-xs text-(--tgui--hint_color)">
        <span>{formatPlaybackMs(positionMs)}</span>
        <span>{playing ? '▶ играет' : '⏸ пауза'}</span>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button mode="filled" size="s" disabled={busy} onClick={onPlay}>
          <Play className="mr-1 inline size-4" />
          Play
        </Button>
        <Button mode="gray" size="s" disabled={busy} onClick={onPause}>
          <Pause className="mr-1 inline size-4" />
          Pause
        </Button>
        <Button mode="gray" size="s" disabled={busy} onClick={onSeek}>
          Seek
        </Button>
        <Button mode="plain" size="s" className="ml-auto!" onClick={onEndSession}>
          Завершить
        </Button>
      </div>
    </div>
  )
}
