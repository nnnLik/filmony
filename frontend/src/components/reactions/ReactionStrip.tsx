import { Avatar } from '@telegram-apps/telegram-ui'
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type RefObject,
} from 'react'
import { createPortal } from 'react-dom'

import { ApiError, formatApiDetail } from '../../api/client'
import type {
  ReactionActor,
  ReactionCatalogItem,
  ReactionGroupedCatalog,
  ReactionSummary,
} from '../../api/profileTypes'
import { setUserReaction } from '../../api/reactionApi'
import { loadReactionActors } from '../../lib/reactionActorsCache'
import { loadReactionCatalog } from '../../lib/reactionCatalogCache'

const EMPTY: ReactionSummary = { counts: [], my_reaction_type_id: null }

const POPOVER_WIDTH = 300
const POPOVER_GAP = 10
const SIDE_PAD = 10

function filterItems(items: ReactionCatalogItem[], q: string): ReactionCatalogItem[] {
  const t = q.trim().toLowerCase()
  if (!t) return items
  return items.filter((item) => {
    const label = (item.label ?? '').toLowerCase()
    const basename = (item.asset_key?.split('/').pop() ?? '').toLowerCase()
    return label.includes(t) || basename.includes(t)
  })
}

function displayActorName(a: ReactionActor): string {
  if (a.display_name && a.display_name.trim() !== '') return a.display_name.trim()
  const u = (a.username ?? '').trim()
  if (u !== '') return `@${u}`
  const parts = [a.first_name, a.last_name].filter(Boolean).join(' ').trim()
  if (parts !== '') return parts
  return a.profile_slug
}

type CountWithActorsProps = {
  targetKind: 'movie_card' | 'movie_card_comment'
  targetId: number
  reactionTypeId: number
  disabled: boolean
  mine: boolean
  imageUrl: string
  label: string | null | undefined
  count: number
  onPick: () => void
}

function CountPill({
  targetKind,
  targetId,
  reactionTypeId,
  disabled,
  mine,
  imageUrl,
  label,
  count,
  onPick,
}: CountWithActorsProps) {
  const [hover, setHover] = useState(false)
  const [actors, setActors] = useState<ReactionActor[] | null>(null)
  const [actorsErr, setActorsErr] = useState<string | null>(null)
  const timer = useRef<number | null>(null)

  useEffect(() => {
    if (!hover) {
      if (timer.current != null) window.clearTimeout(timer.current)
      timer.current = null
      return
    }
    timer.current = window.setTimeout(() => {
      setActorsErr(null)
      setActors(null)
      void (async () => {
        try {
          const rows = await loadReactionActors({
            targetKind,
            targetId,
            reactionTypeId,
          })
          setActors(rows)
        } catch {
          setActorsErr('err')
        }
      })()
    }, 220)
    return () => {
      if (timer.current != null) window.clearTimeout(timer.current)
    }
  }, [hover, reactionTypeId, targetId, targetKind])

  const showBubble = hover && (actors !== null || actorsErr !== null)

  return (
    <div
      className="relative shrink-0"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => {
        setHover(false)
        setActors(null)
        setActorsErr(null)
      }}
    >
      <button
        type="button"
        disabled={disabled}
        onClick={onPick}
        className={`inline-flex cursor-pointer touch-manipulation items-center gap-1 rounded-full px-2 py-0.5 text-[11px] tabular-nums shadow-sm transition-[transform,opacity,box-shadow] active:scale-95 disabled:opacity-50 ${
          mine
            ? 'bg-[color-mix(in_srgb,var(--tgui--link_color)_22%,transparent)] ring-2 ring-[color-mix(in_srgb,var(--tgui--link_color)_55%,transparent)]'
            : 'bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] ring-1 ring-[color-mix(in_srgb,var(--tgui--divider_color)_85%,transparent)]'
        }`}
        title={label ?? undefined}
      >
        <img src={imageUrl} alt="" className="size-[22px] rounded-md object-cover" />
        <span className="pr-0.5 text-(--tgui--text_color)">{count}</span>
      </button>
      {showBubble ? (
        <div
          role="tooltip"
          className="absolute bottom-full left-1/2 z-[90] mb-2 min-w-[168px] max-w-[226px] -translate-x-1/2 rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-2.5 shadow-[0_8px_32px_rgba(0,0,0,0.22)]"
        >
          <p className="mb-1 text-[10px] font-medium text-(--tgui--hint_color)">Кто реагировал</p>
          {actors === null && actorsErr === null ? (
            <p className="text-[10px] text-(--tgui--hint_color)">Загрузка…</p>
          ) : null}
          {actorsErr !== null ? (
            <p className="text-[10px] text-(--tgui--destructive_text_color)">Не удалось загрузить</p>
          ) : null}
          {actors !== null && actors.length === 0 ? (
            <p className="text-[10px] text-(--tgui--hint_color)">Пока никого</p>
          ) : null}
          {actors !== null && actors.length > 0 ? (
            <ul className="flex max-h-28 flex-wrap gap-2 overflow-y-auto">
              {actors.map((a) => (
                <li key={a.id} title={displayActorName(a)} className="flex flex-col items-center gap-0.5">
                  {a.photo_url ? (
                    <Avatar src={a.photo_url} acronym={displayActorName(a).slice(0, 1)} size={28} />
                  ) : (
                    <Avatar acronym={displayActorName(a).slice(0, 2)} size={28} />
                  )}
                  <span className="line-clamp-1 max-w-[56px] text-center text-[9px] text-(--tgui--hint_color)">
                    {displayActorName(a)}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

function usePopoverPosition(triggerRef: RefObject<HTMLButtonElement | null>, open: boolean) {
  const [style, setStyle] = useState<CSSProperties | null>(null)
  const [placeAbove, setPlaceAbove] = useState(true)

  const compute = useCallback(() => {
    const el = triggerRef.current
    if (!el) return
    const r = el.getBoundingClientRect()
    const vw = window.innerWidth
    const cx = r.left + r.width / 2
    let left = cx - POPOVER_WIDTH / 2
    left = Math.max(SIDE_PAD, Math.min(left, vw - POPOVER_WIDTH - SIDE_PAD))

    const minTopSpace = 120
    const placeUp = r.top >= minTopSpace
    setPlaceAbove(placeUp)

    const maxH = placeUp
      ? Math.min(340, Math.max(160, r.top - POPOVER_GAP - 24))
      : Math.min(340, Math.max(160, window.innerHeight - r.bottom - POPOVER_GAP - 24))

    if (placeUp) {
      setStyle({
        position: 'fixed',
        left,
        bottom: `${window.innerHeight - r.top + POPOVER_GAP}px`,
        width: POPOVER_WIDTH,
        maxHeight: maxH,
        zIndex: 200,
      })
    } else {
      setStyle({
        position: 'fixed',
        left,
        top: `${r.bottom + POPOVER_GAP}px`,
        width: POPOVER_WIDTH,
        maxHeight: maxH,
        zIndex: 200,
      })
    }
  }, [triggerRef])

  useLayoutEffect(() => {
    if (!open) {
      setStyle(null)
      return
    }
    compute()
  }, [open, compute])

  useEffect(() => {
    if (!open) return
    const fn = () => compute()
    window.addEventListener('resize', fn)
    window.addEventListener('scroll', fn, true)
    return () => {
      window.removeEventListener('resize', fn)
      window.removeEventListener('scroll', fn, true)
    }
  }, [open, compute])

  return { style, placeAbove }
}

export type ReactionStripProps = {
  targetKind: 'movie_card' | 'movie_card_comment'
  targetId: number
  summary: ReactionSummary | undefined
  onSummaryChange: (next: ReactionSummary) => void
  className?: string
}

export function ReactionStrip({
  targetKind,
  targetId,
  summary,
  onSummaryChange,
  className,
}: ReactionStripProps) {
  const effective = summary ?? EMPTY
  const [pickerOpen, setPickerOpen] = useState(false)
  const [catalog, setCatalog] = useState<ReactionGroupedCatalog | null>(null)
  const [catalogError, setCatalogError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [activeTabSlug, setActiveTabSlug] = useState<string | null>(null)

  const triggerRef = useRef<HTMLButtonElement>(null)
  const { style: popoverStyle, placeAbove } = usePopoverPosition(triggerRef, pickerOpen)

  useEffect(() => {
    if (!pickerOpen) setSearch('')
  }, [pickerOpen])

  useEffect(() => {
    if (!pickerOpen) return undefined
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setPickerOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [pickerOpen])

  useEffect(() => {
    if (!pickerOpen) return undefined
    let alive = true
    setCatalogError(null)
    void (async () => {
      try {
        const grp = await loadReactionCatalog()
        if (alive) setCatalog(grp)
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

  useEffect(() => {
    if (!catalog || catalog.tabs.length === 0) return
    const firstSlug = catalog.tabs.find((x) => x.items.length > 0)?.category_slug ?? catalog.tabs[0].category_slug
    setActiveTabSlug((prev) => {
      if (prev && catalog.tabs.some((t) => t.category_slug === prev)) return prev
      return firstSlug
    })
  }, [catalog])

  const activeTab = useMemo(() => {
    if (!catalog) return null
    return catalog.tabs.find((t) => t.category_slug === activeTabSlug) ?? catalog.tabs[0] ?? null
  }, [activeTabSlug, catalog])

  const gridItems = useMemo(() => filterItems(activeTab?.items ?? [], search), [activeTab?.items, search])
  const recentFiltered = useMemo(() => filterItems(catalog?.recent ?? [], search), [catalog?.recent, search])

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

  const pickerPortal =
    pickerOpen &&
    popoverStyle &&
    typeof document !== 'undefined' &&
    createPortal(
      <>
        <button
          type="button"
          aria-label="Закрыть"
          tabIndex={-1}
          className="fixed inset-0 z-[199] cursor-default bg-black/20"
          onClick={() => setPickerOpen(false)}
        />
        <div
          role="dialog"
          aria-label="Выбор реакции"
          className="fixed z-[200] flex flex-col overflow-hidden rounded-[20px] border border-[color-mix(in_srgb,var(--tgui--divider_color)_90%,transparent)] bg-(--tgui--bg_color) pb-2 pt-2.5 shadow-[0_14px_50px_-8px_rgba(0,0,0,0.45)]"
          style={popoverStyle as CSSProperties}
        >
          <div
            className={`pointer-events-none absolute left-1/2 size-3 -translate-x-1/2 rotate-45 rounded-sm border-[color-mix(in_srgb,var(--tgui--divider_color)_90%,transparent)] bg-(--tgui--bg_color) shadow-sm ${
              placeAbove ? '-bottom-[5px] border-r border-b' : '-top-[5px] border-l border-t'
            }`}
            aria-hidden
          />

          <div className="relative z-[1] flex min-h-0 flex-1 flex-col px-3">
            <input
              type="search"
              placeholder="Найти…"
              autoComplete="off"
              autoCorrect="off"
              spellCheck={false}
              enterKeyHint="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="mb-2.5 w-full rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-2 text-[13px] text-(--tgui--text_color) outline-none placeholder:text-(--tgui--hint_color) focus:ring-2 focus:ring-[color-mix(in_srgb,var(--tgui--link_color)_35%,transparent)]"
            />

            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain [-webkit-overflow-scrolling:touch]">
              {catalogError != null ? (
                <p className="py-6 text-center text-[12px] text-(--tgui--destructive_text_color)">{catalogError}</p>
              ) : null}
              {catalog === null && catalogError == null ? (
                <p className="py-8 text-center text-[13px] text-(--tgui--hint_color)">Загрузка…</p>
              ) : null}
              {catalog != null && recentFiltered.length > 0 ? (
                <>
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-(--tgui--hint_color)">
                    Частые
                  </p>
                  <div className="mb-3 flex gap-2 overflow-x-auto pb-1 [-webkit-overflow-scrolling:touch]">
                    {recentFiltered.map((item) => {
                      const mine = effective.my_reaction_type_id === item.id
                      const badge = countsById.get(item.id)
                      return (
                        <button
                          key={`r-${item.id}`}
                          type="button"
                          disabled={busy}
                          onClick={() => void apply(item.id)}
                          className={`relative shrink-0 rounded-xl p-1 transition-[transform,opacity] active:scale-95 disabled:opacity-50 ${
                            mine ? 'ring-2 ring-(--tgui--link_color)' : 'ring-1 ring-transparent hover:ring-(--tgui--divider_color)'
                          }`}
                        >
                          <img src={item.image_url} alt="" className="size-10 rounded-lg object-cover" />
                          {badge != null ? (
                            <span className="absolute -bottom-1 -right-1 flex min-h-[17px] min-w-[17px] items-center justify-center rounded-full bg-(--tgui--link_color) px-1 text-[9px] font-bold leading-none text-[var(--tgui--button_text_color,white)] shadow-sm tabular-nums">
                              {badge.count}
                            </span>
                          ) : null}
                        </button>
                      )
                    })}
                  </div>
                </>
              ) : catalog != null &&
                catalog.recent.length === 0 &&
                search.trim() === '' ? (
                <p className="mb-3 text-[11px] text-(--tgui--hint_color)">Листайте коллекции ниже.</p>
              ) : null}
              {catalog != null && catalog.tabs.length > 0 ? (
                <>
                  <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-(--tgui--hint_color)">
                    Коллекции
                  </p>
                  <div className="mb-3 flex gap-1.5 overflow-x-auto pb-1 [-webkit-overflow-scrolling:touch]">
                    {catalog.tabs.map((tab) => {
                      const sel = tab.category_slug === (activeTabSlug ?? tab.category_slug)
                      return (
                        <button
                          key={tab.category_slug}
                          type="button"
                          disabled={busy}
                          onClick={() => setActiveTabSlug(tab.category_slug)}
                          className={`shrink-0 rounded-full px-3 py-1.5 text-[12px] font-medium transition-colors ${
                            sel
                              ? 'bg-[color-mix(in_srgb,var(--tgui--link_color)_88%,transparent)] text-[var(--tgui--button_text_color,white)]'
                              : 'bg-(--tgui--secondary_bg_color) text-(--tgui--text_color) active:opacity-90'
                          }`}
                        >
                          {tab.label}
                        </button>
                      )
                    })}
                  </div>
                  {activeTab != null ? (
                    <div className="grid grid-cols-5 gap-1 pb-3">
                      {gridItems.map((item) => {
                        const mine = effective.my_reaction_type_id === item.id
                        return (
                          <button
                            key={item.id}
                            type="button"
                            disabled={busy}
                            onClick={() => void apply(item.id)}
                            title={item.label ?? ''}
                            className={`aspect-square shrink-0 touch-manipulation rounded-xl p-0.5 transition-[transform] active:scale-90 disabled:opacity-50 ${
                              mine ? 'ring-2 ring-(--tgui--link_color) ring-offset-1 ring-offset-(--tgui--bg_color)' : ''
                            }`}
                          >
                            <img src={item.image_url} alt="" className="size-full rounded-lg object-cover" />
                          </button>
                        )
                      })}
                      {gridItems.length === 0 ? (
                        <p className="col-span-5 py-6 text-center text-[12px] text-(--tgui--hint_color)">
                          Ничего не нашлось
                        </p>
                      ) : null}
                    </div>
                  ) : null}
                </>
              ) : null}
            </div>
          </div>
        </div>
      </>,
      document.body,
    )

  return (
    <div className={className}>
      <div className="flex flex-wrap items-center gap-1">
        {effective.counts.map((c) => {
          const mine = effective.my_reaction_type_id === c.reaction_type_id
          return (
            <CountPill
              key={c.reaction_type_id}
              targetKind={targetKind}
              targetId={targetId}
              reactionTypeId={c.reaction_type_id}
              disabled={busy}
              mine={mine}
              imageUrl={c.image_url}
              label={c.label}
              count={c.count}
              onPick={() => void apply(c.reaction_type_id)}
            />
          )
        })}
        <button
          ref={triggerRef}
          type="button"
          disabled={busy}
          onClick={(e) => {
            e.stopPropagation()
            setActionError(null)
            setPickerOpen((v) => !v)
          }}
          aria-expanded={pickerOpen}
          aria-label="Выбрать реакцию"
          className="flex size-8 shrink-0 touch-manipulation items-center justify-center rounded-full bg-(--tgui--secondary_bg_color) text-xl leading-none ring-1 ring-[color-mix(in_srgb,var(--tgui--divider_color)_80%,transparent)] transition-[transform,box-shadow] hover:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] active:scale-90 aria-expanded:bg-[color-mix(in_srgb,var(--tgui--link_color)_22%,transparent)] aria-expanded:ring-[color-mix(in_srgb,var(--tgui--link_color)_40%,transparent)]"
        >
          <span className="relative top-px select-none">😊</span>
        </button>
      </div>
      {actionError != null ? (
        <p className="mt-1 text-[10px] text-(--tgui--destructive_text_color)">{actionError}</p>
      ) : null}
      {pickerPortal}
    </div>
  )
}
