import { Button, IconButton } from '@telegram-apps/telegram-ui'
import { Users, X } from 'lucide-react'
import { createPortal } from 'react-dom'

export type WatchPartyCreateSheetProps = {
  open: boolean
  title: string
  posterUrl: string | null
  busy?: boolean
  onClose: () => void
  onConfirm: () => void
}

export function WatchPartyCreateSheet({
  open,
  title,
  posterUrl,
  busy = false,
  onClose,
  onConfirm,
}: WatchPartyCreateSheetProps) {
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
        <div className="mb-3 flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-wide text-(--tgui--hint_color)">Смотреть вместе</p>
            <h2 className="truncate text-lg font-semibold">{title}</h2>
          </div>
          <IconButton mode="gray" size="s" onClick={onClose} aria-label="Закрыть" disabled={busy}>
            <X className="block size-5" />
          </IconButton>
        </div>
        {posterUrl ? (
          <img src={posterUrl} alt="" className="mb-3 aspect-[2/3] w-24 rounded-lg object-cover" />
        ) : null}
        <p className="mb-4 text-sm text-(--tgui--hint_color)">
          Создайте комнату с чатом и синхронизацией от ведущего. Пригласите друзей по ссылке.
        </p>
        <Button mode="filled" stretched disabled={busy} onClick={onConfirm}>
          <Users className="mr-2 inline size-4" />
          Начать просмотр
        </Button>
      </div>
    </div>,
    document.body,
  )
}
