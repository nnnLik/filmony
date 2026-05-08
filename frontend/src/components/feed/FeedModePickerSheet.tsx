import { Button } from '@telegram-apps/telegram-ui'
import { Check } from 'lucide-react'
import { useEffect } from 'react'

import type { FeedListMode } from '../../api/profileTypes'

export const FEED_MODE_ENTRIES: Array<{
  value: FeedListMode
  title: string
  hint: string
}> = [
  {
    value: 'default',
    title: 'Для вас',
    hint: 'Подписки, подписчики, похожее по тегам и новые авторы',
  },
  {
    value: 'subscriptions_only',
    title: 'Из подписок',
    hint: 'Люди, на которых вы подписаны, и ваши карточки',
  },
  {
    value: 'subscribers_only',
    title: 'От подписчиков',
    hint: 'Те, кто подписан на вас, и ваши карточки',
  },
]

export function feedModeTitle(mode: FeedListMode): string {
  return FEED_MODE_ENTRIES.find((e) => e.value === mode)?.title ?? 'Для вас'
}

export type FeedModePickerSheetProps = {
  open: boolean
  onClose: () => void
  value: FeedListMode
  onSelect: (mode: FeedListMode) => void
}

export function FeedModePickerSheet({ open, onClose, value, onSelect }: FeedModePickerSheetProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex flex-col justify-end">
      <button
        type="button"
        className="absolute inset-0 cursor-default bg-black/50"
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="feed-mode-sheet-title"
        className="relative max-h-[min(85vh,28rem)] overflow-y-auto rounded-t-2xl border border-(--tgui--divider_color) border-b-0 bg-(--tgui--bg_color) px-4 pb-[max(12px,env(safe-area-inset-bottom))] pt-3 shadow-[0_-8px_40px_rgba(0,0,0,0.35)]"
      >
        <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-(--tgui--divider_color)" aria-hidden />
        <h2
          id="feed-mode-sheet-title"
          className="mb-4 text-center text-[15px] font-semibold text-(--tgui--text_color)"
        >
          Что показывать
        </h2>
        <ul className="flex flex-col gap-1 pb-2">
          {FEED_MODE_ENTRIES.map((entry) => {
            const selected = entry.value === value
            return (
              <li key={entry.value}>
                <button
                  type="button"
                  onClick={() => {
                    onSelect(entry.value)
                    onClose()
                  }}
                  className={`flex w-full items-start gap-3 rounded-xl px-3 py-3 text-left transition active:scale-[0.99] ${
                    selected
                      ? 'bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_12%,transparent)] ring-1 ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_45%,transparent)]'
                      : 'bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] hover:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_100%,transparent)]'
                  }`}
                >
                  <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full border border-(--tgui--divider_color) bg-(--tgui--bg_color)">
                    {selected ? (
                      <Check className="size-3.5 text-(--filmony-mint,#5eead4)" strokeWidth={2.5} aria-hidden />
                    ) : null}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-[14px] font-semibold text-(--tgui--text_color)">{entry.title}</span>
                    <span className="mt-0.5 block text-[12px] leading-snug text-(--tgui--hint_color)">
                      {entry.hint}
                    </span>
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
        <div className="pb-1 pt-1">
          <Button mode="gray" stretched size="m" onClick={onClose}>
            Закрыть
          </Button>
        </div>
      </div>
    </div>
  )
}
