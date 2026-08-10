import { Button } from '@telegram-apps/telegram-ui'
import { Pause, Play } from 'lucide-react'

export type WatchPartyHostSyncBarProps = {
  busy: boolean
  playing: boolean
  onPlayAll: () => void
  onPauseAll: () => void
  onEndSession: () => void
}

export function WatchPartyHostSyncBar({
  busy,
  playing,
  onPlayAll,
  onPauseAll,
  onEndSession,
}: WatchPartyHostSyncBarProps) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">
      <p className="mb-2 text-[11px] text-(--tgui--hint_color)">
        Управляйте своим плеером как обычно. Кнопки ниже — сигнал гостям (пауза / play).
      </p>
      <div className="flex flex-wrap items-center gap-2">
      <Button
        mode="gray"
        size="s"
        disabled={busy || !playing}
        onClick={onPauseAll}
      >
        <Pause className="mr-1 inline size-4" />
        Пауза для всех
      </Button>
      <Button
        mode="filled"
        size="s"
        disabled={busy || playing}
        onClick={onPlayAll}
      >
        <Play className="mr-1 inline size-4" />
        Play для всех
      </Button>
      <Button mode="plain" size="s" className="ml-auto!" onClick={onEndSession}>
        Завершить
      </Button>
      </div>
    </div>
  )
}
