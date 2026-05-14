import { IconButton } from '@telegram-apps/telegram-ui'
import { Clapperboard } from 'lucide-react'
import { useCallback, useEffect, useRef, useState, type MouseEvent } from 'react'
import { createPortal } from 'react-dom'

import { listWatchedInlinePicker, type WatchedInlinePickerItem } from '../../api/cardApi'
import { ApiError, formatApiDetail } from '../../api/client'
import { PICK_BG, PICK_BORDER, POPOVER_W_COMPACT } from '../reactions/reactionStrip/constants'
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
  const { style: popoverStyle } = usePopoverPosition(triggerRef, open, POPOVER_W_COMPACT)

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
      <>
        <button
          type="button"
          aria-label="Закрыть"
          tabIndex={-1}
          className="fixed inset-0 z-199 cursor-default bg-black/72"
          onMouseDown={(e) => {
            e.preventDefault()
            close()
          }}
        />
        <div
          role="dialog"
          aria-label="Выбор своей карточки для вставки"
          className={`max-h-[min(70vh,22rem)] overflow-hidden rounded-xl border shadow-[0_16px_48px_rgba(0,0,0,0.55)] border ${PICK_BORDER} ${PICK_BG}`}
          style={{
            ...popoverStyle,
            color: 'var(--tgui--text_color, #eaeaea)',
          }}
          onMouseDown={(e) => e.preventDefault()}
        >
          <div className={`border-b p-2 border-[#2c2c2e]`}>
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Название темы…"
              className="w-full rounded-lg border border-[#2c2c2e] bg-[#1c1c1f] px-2 py-1.5 text-[13px] text-zinc-100 outline-none placeholder:text-zinc-500 focus:border-[color-mix(in_srgb,var(--tgui--link_color)_65%,#2c2c2e)]"
              autoFocus
            />
          </div>
          <div className="max-h-[min(55vh,18rem)] overflow-y-auto">
            {error != null ? (
              <p className="px-3 py-2 text-[12px] text-red-400">{error}</p>
            ) : loading ? (
              <p className="px-3 py-2 text-[12px] text-zinc-500">Загрузка…</p>
            ) : items.length === 0 ? (
              <p className="px-3 py-2 text-[12px] text-zinc-500">Ничего не найдено</p>
            ) : (
              items.map((it) => (
                <button
                  key={it.movie_card_id}
                  type="button"
                  className="flex w-full flex-col gap-0.5 border-b border-[#2c2c2e] px-3 py-2 text-left transition last:border-b-0 hover:bg-[#252528] active:bg-[#2a2a2e]"
                  onMouseDown={(e) => {
                    e.preventDefault()
                    onPick(it)
                    close()
                    setQ('')
                  }}
                >
                  <span className="text-[13px] font-medium text-zinc-100">{it.film_title}</span>
                  <span className="text-[11px] text-zinc-500">
                    {it.film_year != null ? `${it.film_year} · ` : ''}карточка #{it.movie_card_id}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>
      </>,
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
        aria-label="Вставить ссылку на свою карточку"
        className="relative z-0 box-border! flex! h-8! w-8! min-h-8! min-w-8! shrink-0 items-center! justify-center! rounded-full p-0! leading-none! text-(--tgui--hint_color)"
      >
        <Clapperboard className="relative z-1 block size-[18px] shrink-0" strokeWidth={1.75} aria-hidden />
      </IconButton>
      {portal}
    </>
  )
}
