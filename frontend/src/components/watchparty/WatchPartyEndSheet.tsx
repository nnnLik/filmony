import { Button, IconButton } from '@telegram-apps/telegram-ui'
import { X } from 'lucide-react'
import { createPortal } from 'react-dom'

export type WatchPartyEndSheetProps = {
  open: boolean
  busy?: boolean
  onClose: () => void
  onEndOnly: () => void
  onEndAndRateTogether: () => void
}

export function WatchPartyEndSheet({
  open,
  busy = false,
  onClose,
  onEndOnly,
  onEndAndRateTogether,
}: WatchPartyEndSheetProps) {
  if (!open) {
    return null
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
          <h2 className="text-lg font-semibold">Завершить сеанс?</h2>
          <IconButton mode="gray" size="s" onClick={onClose} aria-label="Закрыть" disabled={busy}>
            <X className="block size-5" />
          </IconButton>
        </div>
        <p className="mb-4 text-sm text-(--tgui--hint_color)">
          Можно просто закрыть комнату или сразу перейти к совместной оценке фильма.
        </p>
        <div className="flex flex-col gap-2">
          <Button stretched disabled={busy} onClick={onEndAndRateTogether}>
            Завершить и оценить вместе
          </Button>
          <Button mode="gray" stretched disabled={busy} onClick={onEndOnly}>
            Завершить
          </Button>
          <Button mode="plain" stretched disabled={busy} onClick={onClose}>
            Отмена
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
