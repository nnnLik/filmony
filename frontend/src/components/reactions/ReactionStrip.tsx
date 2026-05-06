import { Button } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { ApiError, formatApiDetail } from '../../api/client'
import type { ReactionCatalogItem, ReactionSummary } from '../../api/profileTypes'
import { setUserReaction } from '../../api/reactionApi'
import { loadReactionCatalogItems } from '../../lib/reactionCatalogCache'

const EMPTY: ReactionSummary = { counts: [], my_reaction_type_id: null }

export type ReactionStripProps = {
  targetKind: 'movie_card' | 'movie_card_comment'
  targetId: number
  summary: ReactionSummary | undefined
  onSummaryChange: (next: ReactionSummary) => void
  className?: string
}

export function ReactionStrip({ targetKind, targetId, summary, onSummaryChange, className }: ReactionStripProps) {
  const effective = summary ?? EMPTY
  const [pickerOpen, setPickerOpen] = useState(false)
  const [catalog, setCatalog] = useState<ReactionCatalogItem[] | null>(null)
  const [catalogError, setCatalogError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  useEffect(() => {
    if (!pickerOpen) return
    let alive = true
    setCatalogError(null)
    void (async () => {
      try {
        const items = await loadReactionCatalogItems()
        if (alive) setCatalog(items)
      } catch (e) {
        if (alive) {
          setCatalogError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось загрузить реакции')
        }
      }
    })()
    return () => {
      alive = false
    }
  }, [pickerOpen])

  const apply = useCallback(
    async (reactionTypeId: number) => {
      setBusy(true)
      setActionError(null)
      try {
        const res = await setUserReaction({
          target_kind: targetKind,
          target_id: targetId,
          reaction_type_id: reactionTypeId,
        })
        onSummaryChange(res.reactions)
        setPickerOpen(false)
      } catch (e) {
        setActionError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось применить')
      } finally {
        setBusy(false)
      }
    },
    [onSummaryChange, targetId, targetKind]
  )

  const countsById = useMemo(() => {
    const m = new Map<number, (typeof effective.counts)[0]>()
    effective.counts.forEach((c) => m.set(c.reaction_type_id, c))
    return m
  }, [effective.counts])

  return (
    <div className={className}>
      <div className="flex flex-wrap items-center gap-1.5">
        {effective.counts.map((c) => {
          const mine = effective.my_reaction_type_id === c.reaction_type_id
          return (
            <button
              key={c.reaction_type_id}
              type="button"
              disabled={busy}
              onClick={() => void apply(c.reaction_type_id)}
              className={`inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[11px] tabular-nums transition active:opacity-90 ${
                mine
                  ? 'border-(--tgui--link_color) bg-[color-mix(in_srgb,var(--tgui--link_color)_12%,transparent)]'
                  : 'border-(--tgui--divider_color) bg-(--tgui--bg_color)'
              }`}
              title={c.label ?? undefined}
            >
              <img src={c.image_url} alt="" className="size-5 rounded object-cover" />
              <span className="text-(--tgui--text_color)">{c.count}</span>
            </button>
          )
        })}
        <Button
          mode="outline"
          size="s"
          type="button"
          disabled={busy}
          className="min-h-7! min-w-7! px-0! text-sm"
          onClick={() => {
            setActionError(null)
            setPickerOpen(true)
          }}
          aria-label="Выбрать реакцию"
        >
          +
        </Button>
      </div>
      {actionError != null ? <p className="mt-1 text-[10px] text-(--tgui--destructive_text_color)">{actionError}</p> : null}

      {pickerOpen ? (
        <div
          className="fixed inset-0 z-120 flex items-end justify-center bg-black/50 p-2"
          role="presentation"
          onClick={() => setPickerOpen(false)}
          onKeyDown={(e) => {
            if (e.key === 'Escape') setPickerOpen(false)
          }}
        >
          <div
            role="dialog"
            aria-label="Каталог реакций"
            className="mb-[max(0.5rem,env(safe-area-inset-bottom))] max-h-[60vh] w-full max-w-sm overflow-y-auto rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-(--tgui--text_color)">Реакция</p>
              <button
                type="button"
                className="text-xs text-(--tgui--link_color)"
                onClick={() => setPickerOpen(false)}
              >
                Закрыть
              </button>
            </div>
            {catalogError != null ? (
              <p className="text-xs text-(--tgui--destructive_text_color)">{catalogError}</p>
            ) : null}
            {catalog == null && catalogError == null ? (
              <p className="text-xs text-(--tgui--hint_color)">Загрузка…</p>
            ) : null}
            {catalog != null ? (
              <div className="grid grid-cols-4 gap-3">
                {catalog.map((item) => {
                  const count = countsById.get(item.id)?.count ?? 0
                  const mine = effective.my_reaction_type_id === item.id
                  return (
                    <button
                      key={item.id}
                      type="button"
                      disabled={busy}
                      onClick={() => void apply(item.id)}
                      className={`flex flex-col items-center gap-1 rounded-xl p-1 transition active:opacity-90 ${
                        mine ? 'ring-2 ring-(--tgui--link_color)' : 'ring-1 ring-(--tgui--divider_color)'
                      }`}
                    >
                      <img
                        src={item.image_url}
                        alt=""
                        className="size-12 rounded-lg object-cover"
                      />
                      {item.label != null && item.label.trim() !== '' ? (
                        <span className="line-clamp-2 text-center text-[10px] text-(--tgui--hint_color)">
                          {item.label}
                        </span>
                      ) : null}
                      {count > 0 ? (
                        <span className="text-[10px] tabular-nums text-(--tgui--hint_color)">{count}</span>
                      ) : null}
                    </button>
                  )
                })}
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  )
}
