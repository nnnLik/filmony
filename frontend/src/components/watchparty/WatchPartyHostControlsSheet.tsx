import { Button, IconButton } from '@telegram-apps/telegram-ui'
import { Pause, Play, X } from 'lucide-react'
import { useState } from 'react'
import { createPortal } from 'react-dom'

import { formatPlaybackMs } from '../../lib/watchPartyTime'

export type WatchPartyHostControlsSheetProps = {
  open: boolean
  busy: boolean
  playing: boolean
  positionMs: number
  onClose: () => void
  onPositionChange: (ms: number) => void
  onPlay: () => void
  onPause: () => void
  onSeek: () => void
  onCountdownStart: () => void
  onEndSession: () => void
  onOpenInBrowser?: () => void
}

export function WatchPartyHostControlsSheet({
  open,
  busy,
  playing,
  positionMs,
  onClose,
  onPositionChange,
  onPlay,
  onPause,
  onSeek,
  onCountdownStart,
  onEndSession,
  onOpenInBrowser,
}: WatchPartyHostControlsSheetProps) {
  const [countdown, setCountdown] = useState<number | null>(null)

  if (!open) {
    return null
  }

  const startCountdown = () => {
    let remaining = 3
    setCountdown(remaining)
    const tick = () => {
      remaining -= 1
      if (remaining <= 0) {
        setCountdown(null)
        onCountdownStart()
        return
      }
      setCountdown(remaining)
      window.setTimeout(tick, 1000)
    }
    window.setTimeout(tick, 1000)
  }

  return createPortal(
    <div className="filmony-theme fixed inset-0 z-50 flex flex-col justify-end text-(--tgui--text_color) pointer-events-auto">
      <button
        type="button"
        className="absolute inset-0 bg-[color-mix(in_srgb,var(--filmony-ink,#06090d)_72%,transparent)]"
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div
        className="relative z-10 mx-auto w-full max-w-md rounded-t-[22px] border border-(--tgui--divider_color) bg-(--tgui--tertiary_bg_color) p-4 shadow-[0_-16px_48px_rgba(0,0,0,0.5)]"
        role="dialog"
        aria-modal="true"
      >
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">Управление</h2>
          <IconButton mode="gray" size="s" onClick={onClose} aria-label="Закрыть">
            <X className="block size-5" />
          </IconButton>
        </div>
        {countdown != null ? (
          <p className="mb-3 text-center text-3xl font-bold">{countdown}</p>
        ) : null}
        <input
          type="range"
          min={0}
          max={7_200_000}
          step={1000}
          value={positionMs}
          onChange={(e) => onPositionChange(Number(e.target.value))}
          className="mb-2 w-full"
        />
        <div className="mb-3 flex items-center justify-between text-xs text-(--tgui--hint_color)">
          <span>{formatPlaybackMs(positionMs)}</span>
          <span>{playing ? '▶' : '⏸'}</span>
        </div>
        <div className="flex flex-wrap gap-2">
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
          <Button mode="bezeled" size="s" onClick={startCountdown}>
            Старт 3-2-1
          </Button>
        </div>
        <div className="mt-3 flex flex-col gap-2">
          {onOpenInBrowser != null ? (
            <Button mode="gray" stretched onClick={onOpenInBrowser}>
              Открыть в браузере
            </Button>
          ) : null}
          <Button mode="plain" stretched onClick={onEndSession}>
            Завершить сеанс
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
