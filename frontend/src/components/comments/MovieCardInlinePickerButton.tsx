import { IconButton } from '@telegram-apps/telegram-ui'
import { Clapperboard } from 'lucide-react'
import { useCallback, useEffect, useRef, useState, type MouseEvent } from 'react'
import { createPortal } from 'react-dom'

import { listWatchedInlinePicker, type WatchedInlinePickerItem } from '../../api/cardApi'
import { ApiError, formatApiDetail } from '../../api/client'
import { POPOVER_W_COMPACT } from '../reactions/reactionStrip/constants'
import { usePopoverPosition } from '../reactions/reactionStrip/usePopoverPosition'

export type MovieCardInlinePickerButtonProps = {
  onPick: (row: WatchedInlinePickerItem) => void
  disabled?: boolean
  allowInsert?: boolean
}

export function MovieCardInlinePickerButton({
  onPick,
  disabled = false,
  allowInsert = true,
}: MovieCardInlinePickerButtonProps) {
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState('')
  const [items, setItems] = useState<WatchedInlinePickerItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const { style: popoverStyle, placeAbove } = usePopoverPosition(triggerRef, open, POPOVER_W_COMPACT)

  const close = useCallback(() => {
    setOpen(false)
  }, [])

  useEffect(() => {
    if (!open) return undefined
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, close])

  useEffect(() => {
    if (!open) return undefined
    let alive = true
    const t = window.setTimeout(() => {
      setLoading(true)
      setError(null)
      void listWatchedInlinePicker({ q, limit: 40 })
        .then((res) => {
          if (!alive) return
          setItems(res.items)
        })
        .catch((e: unknown) => {
          if (!alive) return
          setItems([])
          setError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить')
        })
        .finally(() => {
          if (alive) setLoading(false)
        })
    }, 200)
    return () => {
      alive = false
      window.clearTimeout(t)
    }
  }, [open, q])

  const blocked = disabled || !allowInsert

  const portal =
    open &&
    popoverStyle &&
    typeof document !== 'undefined' &&
    createPortal(
      <div
        role="dialog"
        aria-label="Выбор карточки фильма"
        className="z-200 max-h-[min(70vh,22rem)] w-[min(92vw,20rem)] overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) shadow-lg"
        style={{
          position: 'fixed',
          top: placeAbove ? undefined : popoverStyle.top,
          bottom: placeAbove ? `calc(100vh - ${popoverStyle.top}px)` : undefined,
          left: popoverStyle.left,
          width: popoverStyle.width,
          maxHeight: popoverStyle.maxHeight,
        }}
        onMouseDown={(e) => e.preventDefault()}
      >
        <div className="border-b border-(--tgui--divider_color) p-2">
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Название фильма…"
            className="w-full rounded-lg border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-2 py-1.5 text-[13px] text-(--tgui--text_color) outline-none focus:border-(--tgui--link_color)"
            autoFocus
          />
        </div>
        <div className="max-h-[min(55vh,18rem)] overflow-y-auto">
          {error != null ? (
            <p className="px-3 py-2 text-[12px] text-(--tgui--destructive_text_color)">{error}</p>
          ) : loading ? (
            <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Загрузка…</p>
          ) : items.length === 0 ? (
            <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Ничего не найдено</p>
          ) : (
            items.map((it) => (
              <button
                key={it.movie_card_id}
                type="button"
                className="flex w-full flex-col gap-0.5 border-b border-(--tgui--divider_color) px-3 py-2 text-left transition last:border-b-0 hover:bg-[color-mix(in_srgb,var(--tgui--hint_color)_08%,var(--tgui--secondary_bg_color))] active:bg-[color-mix(in_srgb,var(--tgui--hint_color)_12%,var(--tgui--secondary_bg_color))]"
                onMouseDown={(e) => {
                  e.preventDefault()
                  onPick(it)
                  close()
                  setQ('')
                }}
              >
                <span className="text-[13px] font-medium text-(--tgui--text_color)">{it.film_title}</span>
                <span className="text-[11px] text-(--tgui--hint_color)">
                  {it.film_year != null ? `${it.film_year} · ` : ''}карточка #{it.movie_card_id}
                </span>
              </button>
            ))
          )}
        </div>
      </div>,
      document.body,
    )

  return (
    <>
      <IconButton
        ref={triggerRef}
        type="button"
        size="s"
        mode="gray"
        disabled={blocked}
        onClick={(e: MouseEvent<HTMLButtonElement>) => {
          e.stopPropagation()
          if (blocked) return
          setOpen((v) => !v)
        }}
        aria-expanded={open}
        aria-label="Вставить ссылку на свою карточку фильма"
        className="relative z-0 box-border! flex! h-8! w-8! min-h-8! min-w-8! shrink-0 items-center! justify-center! rounded-full p-0! leading-none! text-(--tgui--hint_color)"
      >
        <Clapperboard className="relative z-1 block size-[18px] shrink-0" strokeWidth={1.75} aria-hidden />
      </IconButton>
      {portal}
    </>
  )
}
