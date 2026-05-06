import { Avatar, IconButton } from '@telegram-apps/telegram-ui'
import { Smile } from 'lucide-react'
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type MouseEvent,
  type RefObject,
} from 'react'
import { createPortal } from 'react-dom'

import { ApiError, formatApiDetail } from '../../api/client'
import type {
  ReactionActor,
  ReactionGroupedCatalog,
  ReactionSummary,
} from '../../api/profileTypes'
import { setUserReaction } from '../../api/reactionApi'
import { loadReactionActors } from '../../lib/reactionActorsCache'
import { clearReactionCatalogCache, loadReactionCatalog } from '../../lib/reactionCatalogCache'
import { resolveApiMediaUrl } from '../../lib/resolveApiMediaUrl'

const EMPTY: ReactionSummary = { counts: [], my_reaction_type_ids: [] }

const POPOVER_GAP = 10
const SIDE_PAD = 10
const POPOVER_W_DEFAULT = 300
const POPOVER_W_COMPACT = 264

/** Непрозрачная палитра попапа (как эталон Telegram). */
const PICK_BG = 'bg-[#121212]'
const PICK_SURFACE = 'bg-[#1c1c1f]'
const PICK_BORDER = 'border-[#2c2c2e]'

function displayActorName(a: ReactionActor): string {
  if (a.display_name && a.display_name.trim() !== '') return a.display_name.trim()
  const u = (a.username ?? '').trim()
  if (u !== '') return `@${u}`
  const parts = [a.first_name, a.last_name].filter(Boolean).join(' ').trim()
  if (parts !== '') return parts
  return a.profile_slug
}

function ReactionThumb({
  src,
  className,
  roundedClassName = 'rounded-lg',
}: {
  src: string
  className: string
  roundedClassName?: string
}) {
  const [failed, setFailed] = useState(false)

  const resolved = useMemo(() => resolveApiMediaUrl(src), [src])

  if (failed) {
    return (
      <div
        className={`animate-pulse bg-[color-mix(in_srgb,var(--tgui--divider_color)_45%,transparent)] ${roundedClassName} ${className}`}
        aria-hidden
      />
    )
  }

  return (
    <img
      src={resolved}
      alt=""
      className={`${roundedClassName} border-0 object-cover outline-none ${className}`}
      onError={() => setFailed(true)}
    />
  )
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
  compact: boolean
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
  compact,
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
        className={
          compact
            ? `inline-flex h-10 min-h-10 cursor-pointer touch-manipulation items-center gap-1.5 rounded-full px-1.5 py-px text-[14px] leading-none tabular-nums ring-[0.5px] transition-[transform,opacity] active:scale-[0.97] disabled:opacity-50 ${
                mine
                  ? 'bg-[color-mix(in_srgb,var(--tgui--link_color)_14%,var(--tgui--secondary_bg_color))] ring-[color-mix(in_srgb,var(--tgui--link_color)_32%,transparent)]'
                  : 'bg-[color-mix(in_srgb,var(--tgui--hint_color)_06%,var(--tgui--secondary_bg_color))] ring-[color-mix(in_srgb,var(--tgui--divider_color)_38%,transparent)]'
              }`
            : `inline-flex h-[22px] min-h-[22px] cursor-pointer touch-manipulation items-center gap-0.5 rounded-full px-1 py-px text-[10px] leading-none tabular-nums ring-1 transition-[transform,opacity] active:scale-[0.98] disabled:opacity-50 ${
                mine
                  ? 'bg-[color-mix(in_srgb,var(--tgui--link_color)_18%,var(--tgui--secondary_bg_color))] ring-[color-mix(in_srgb,var(--tgui--link_color)_38%,transparent)]'
                  : 'bg-[color-mix(in_srgb,var(--tgui--hint_color)_06%,var(--tgui--secondary_bg_color))] ring-[color-mix(in_srgb,var(--tgui--divider_color)_42%,transparent)]'
              }`
        }
        title={label ?? undefined}
      >
        <span
          className={
            compact
              ? 'relative flex size-[30px] shrink-0 overflow-hidden rounded-full'
              : 'flex shrink-0 items-center justify-center rounded-[4px] p-px'
          }
        >
          <ReactionThumb
            src={imageUrl}
            className={compact ? 'size-full object-cover' : 'size-[15px]'}
            roundedClassName={compact ? 'rounded-full' : 'rounded-[4px]'}
          />
        </span>
        <span className={`leading-none text-(--tgui--text_color) ${compact ? 'pr-px' : 'pr-0.5'}`}>{count}</span>
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

function usePopoverPosition(
  triggerRef: RefObject<HTMLButtonElement | null>,
  open: boolean,
  popoverWidth: number,
) {
  const [style, setStyle] = useState<CSSProperties | null>(null)
  const [placeAbove, setPlaceAbove] = useState(true)

  const compute = useCallback(() => {
    const el = triggerRef.current
    if (!el) return
    const r = el.getBoundingClientRect()
    const vw = window.innerWidth
    const cx = r.left + r.width / 2
    let left = cx - popoverWidth / 2
    left = Math.max(SIDE_PAD, Math.min(left, vw - popoverWidth - SIDE_PAD))

    const minTopSpace = 112
    const placeUp = r.top >= minTopSpace
    setPlaceAbove(placeUp)

    const maxH = placeUp
      ? Math.min(300, Math.max(148, r.top - POPOVER_GAP - 20))
      : Math.min(300, Math.max(148, window.innerHeight - r.bottom - POPOVER_GAP - 20))

    if (placeUp) {
      setStyle({
        position: 'fixed',
        left,
        bottom: `${window.innerHeight - r.top + POPOVER_GAP}px`,
        width: popoverWidth,
        maxHeight: maxH,
        zIndex: 200,
      })
    } else {
      setStyle({
        position: 'fixed',
        left,
        top: `${r.bottom + POPOVER_GAP}px`,
        width: popoverWidth,
        maxHeight: maxH,
        zIndex: 200,
      })
    }
  }, [popoverWidth, triggerRef])

  useLayoutEffect(() => {
    if (!open) return
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

  return { style: open ? style : null, placeAbove }
}

export type ReactionStripProps = {
  targetKind: 'movie_card' | 'movie_card_comment'
  targetId: number
  summary: ReactionSummary | undefined
  onSummaryChange: (next: ReactionSummary) => void
  className?: string
  /** Один узкий ряд под текстом комментария (крупнее кружки‑реакции). */
  compact?: boolean
}

export function ReactionStrip({
  targetKind,
  targetId,
  summary,
  onSummaryChange,
  className,
  compact = false,
}: ReactionStripProps) {
  const effective = summary ?? EMPTY
  const myReactionIds = useMemo(
    () => new Set(effective.my_reaction_type_ids),
    [effective.my_reaction_type_ids],
  )
  const popoverW = compact ? POPOVER_W_COMPACT : POPOVER_W_DEFAULT
  const [pickerOpen, setPickerOpen] = useState(false)
  const [catalog, setCatalog] = useState<ReactionGroupedCatalog | null>(null)
  const [catalogError, setCatalogError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [activeTabSlug, setActiveTabSlug] = useState<string | null>(null)

  const triggerRef = useRef<HTMLButtonElement>(null)
  const { style: popoverStyle, placeAbove } = usePopoverPosition(triggerRef, pickerOpen, popoverW)

  const closePicker = useCallback(() => {
    setPickerOpen(false)
  }, [])

  useEffect(() => {
    if (!pickerOpen) return undefined
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closePicker()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [pickerOpen, closePicker])

  useEffect(() => {
    if (!pickerOpen) return undefined
    let alive = true
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

  const effectiveTabSlug = useMemo(() => {
    if (!catalog || catalog.tabs.length === 0) return null
    if (activeTabSlug && catalog.tabs.some((t) => t.category_slug === activeTabSlug)) return activeTabSlug
    return catalog.tabs.find((x) => x.items.length > 0)?.category_slug ?? catalog.tabs[0].category_slug
  }, [catalog, activeTabSlug])

  const activeTab = useMemo(() => {
    if (!catalog || !effectiveTabSlug) return null
    return catalog.tabs.find((t) => t.category_slug === effectiveTabSlug) ?? null
  }, [catalog, effectiveTabSlug])

  const gridItems = activeTab?.items ?? []
  const recentItems = catalog?.recent ?? []

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
        clearReactionCatalogCache()
        closePicker()
      } catch (e) {
        setActionError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось применить')
      } finally {
        setBusy(false)
      }
    },
    [closePicker, onSummaryChange, targetId, targetKind]
  )

  const countsById = useMemo(() => {
    const m = new Map<number, (typeof effective.counts)[0]>()
    effective.counts.forEach((c) => m.set(c.reaction_type_id, c))
    return m
  }, [effective])

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
          className="fixed inset-0 z-199 cursor-default bg-black/72"
          onClick={closePicker}
        />
        <div
          role="dialog"
          aria-label="Выбор реакции"
          className={`fixed z-200 flex flex-col overflow-hidden rounded-[20px] border ${PICK_BORDER} ${PICK_BG} shadow-[0_16px_48px_rgba(0,0,0,0.55)]`}
          style={popoverStyle}
        >
          <div
            className={`pointer-events-none absolute left-1/2 size-3 -translate-x-1/2 rotate-45 ${PICK_BORDER} ${PICK_BG} border shadow-sm ${
              placeAbove ? 'bottom-[-5px] border-r border-b border-t-0 border-l-0' : '-top-[5px] border-l border-t border-r-0 border-b-0'
            }`}
            aria-hidden
          />

          <div className="relative z-1 flex min-h-0 flex-1 flex-col px-2.5 pt-2.5 pb-2">
            <div className="flex min-h-0 flex-1 gap-0 overflow-hidden">
              {catalogError != null ? (
                <p className="w-full px-2 py-6 text-center text-[12px] text-red-400">{catalogError}</p>
              ) : null}
              {catalog === null && catalogError == null ? (
                <p className="w-full px-2 py-8 text-center text-[13px] text-zinc-500">Загрузка…</p>
              ) : null}
              {catalog != null && catalog.tabs.length > 0 ? (
                <>
                  <nav
                    className={`flex w-[76px] shrink-0 flex-col gap-1 overflow-y-auto overscroll-contain border-r pb-1 pl-1 pr-2 [-webkit-overflow-scrolling:touch] ${PICK_BORDER}`}
                  >
                    <span className="px-1.5 pb-0.5 text-[9px] font-semibold uppercase tracking-wide text-zinc-500">
                      Коллекции
                    </span>
                    {catalog.tabs.map((tab) => {
                      const sel = tab.category_slug === effectiveTabSlug
                      return (
                        <button
                          key={tab.category_slug}
                          type="button"
                          disabled={busy}
                          onClick={() => setActiveTabSlug(tab.category_slug)}
                          className={`rounded-lg px-2 py-2 text-left text-[12px] font-medium transition-colors disabled:opacity-50 ${
                            sel
                              ? `${PICK_SURFACE} font-semibold text-white`
                              : 'text-zinc-400 hover:bg-[#252528] hover:text-zinc-200'
                          }`}
                        >
                          {tab.label}
                        </button>
                      )
                    })}
                  </nav>

                  <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-2 overflow-y-auto overscroll-contain pl-3 pr-0.5 [-webkit-overflow-scrolling:touch]">
                    {recentItems.length > 0 ? (
                      <div className="shrink-0">
                        <p className="mb-1.5 text-[11px] font-medium tracking-tight text-zinc-200">
                          Недавние
                        </p>
                        <div className="-mx-0.5 flex gap-1 overflow-x-auto pb-1 [-webkit-overflow-scrolling:touch]">
                          {recentItems.map((item) => {
                            const mine = myReactionIds.has(item.id)
                            const badge = countsById.get(item.id)
                            return (
                              <button
                                key={`r-${item.id}`}
                                type="button"
                                disabled={busy}
                                onClick={() => void apply(item.id)}
                                className={`relative shrink-0 rounded-lg p-[2px] transition-[transform,opacity] active:scale-95 disabled:opacity-50 ${
                                  mine
                                    ? 'ring-2 ring-[#4ade80]'
                                    : 'ring-1 ring-transparent hover:ring-zinc-600'
                                }`}
                              >
                                <ReactionThumb
                                  src={item.image_url}
                                  className={compact ? 'size-12' : 'size-9'}
                                  roundedClassName="rounded-md"
                                />
                                {badge != null ? (
                                  <span className="absolute -bottom-0.5 -right-0.5 flex min-h-[14px] min-w-[14px] items-center justify-center rounded-full bg-emerald-500 px-0.5 text-[8px] font-bold leading-none text-white shadow-sm tabular-nums">
                                    {badge.count}
                                  </span>
                                ) : null}
                              </button>
                            )
                          })}
                        </div>
                      </div>
                    ) : catalog.recent.length === 0 ? (
                      <p className="shrink-0 text-[11px] text-zinc-500">Выберите коллекцию слева.</p>
                    ) : null}

                    {activeTab != null ? (
                      <div className="flex min-h-[80px] min-w-0 flex-1 flex-col">
                        <p className="mb-1.5 shrink-0 text-[11px] font-medium tracking-tight text-zinc-200">
                          {activeTab.label}
                        </p>
                        <div className={`grid shrink-0 gap-1 pb-2 ${compact ? 'grid-cols-3 sm:grid-cols-4' : 'grid-cols-5'}`}>
                          {gridItems.map((item) => {
                            const mine = myReactionIds.has(item.id)
                            return (
                              <button
                                key={item.id}
                                type="button"
                                disabled={busy}
                                onClick={() => void apply(item.id)}
                                title={item.label ?? ''}
                                className={`aspect-square shrink-0 touch-manipulation rounded-lg p-[2px] transition-transform active:scale-90 disabled:opacity-40 ${
                                  mine
                                    ? 'ring-2 ring-[#4ade80] ring-offset-1 ring-offset-[#121212]'
                                    : 'ring-0 hover:ring-1 hover:ring-zinc-600'
                                }`}
                              >
                                <ReactionThumb src={item.image_url} className="size-full" roundedClassName="rounded-md" />
                              </button>
                            )
                          })}
                          {gridItems.length === 0 ? (
                            <p className="col-span-full py-8 text-center text-[12px] text-zinc-500">
                              Ничего не нашлось
                            </p>
                          ) : null}
                        </div>
                      </div>
                    ) : null}
                  </div>
                </>
              ) : null}
            </div>
          </div>
        </div>
      </>,
      document.body,
    )

  return (
    <div className={compact ? `${className ?? ''} min-w-0 flex-1` : className}>
      <div
        className={
          compact
            ? 'flex min-h-10 w-full max-w-full min-w-0 flex-nowrap items-center gap-x-1 gap-y-0 overflow-x-auto pb-px [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden'
            : 'flex flex-wrap items-center gap-1'
        }
      >
        {effective.counts.map((c) => {
          const mine = myReactionIds.has(c.reaction_type_id)
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
              compact={compact}
              onPick={() => void apply(c.reaction_type_id)}
            />
          )
        })}
        <IconButton
          ref={triggerRef}
          type="button"
          size="s"
          mode="gray"
          disabled={busy}
          onClick={(e: MouseEvent<HTMLButtonElement>) => {
            e.stopPropagation()
            setPickerOpen((wasOpen) => {
              if (wasOpen) {
                return false
              }
              setActionError(null)
              setCatalog(null)
              setCatalogError(null)
              return true
            })
          }}
          aria-expanded={pickerOpen}
          aria-label="Выбрать реакцию"
          className={
            compact
              ? 'relative z-0 box-border! flex! h-11! w-11! min-h-11! min-w-11! shrink-0 items-center! justify-center! rounded-full p-0! leading-none! text-(--tgui--hint_color) transition-[transform,colors] hover:text-(--tgui--text_color) active:scale-[0.97] aria-expanded:text-(--tgui--link_color)!'
              : 'relative z-0 box-border! flex! h-9! w-9! min-h-9! min-w-9! shrink-0 items-center! justify-center! rounded-full p-0! leading-none! text-(--tgui--hint_color) transition-[transform,colors] hover:text-(--tgui--text_color) active:scale-[0.98] aria-expanded:text-(--tgui--link_color)!'
          }
        >
          <Smile
            className={`relative z-1 block shrink-0 ${compact ? 'size-[26px]' : 'size-[18px]'}`}
            strokeWidth={1.75}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden
          />
        </IconButton>
      </div>
      {actionError != null ? (
        <p className={`text-(--tgui--destructive_text_color) ${compact ? 'mt-0.5 text-[9px]' : 'mt-1 text-[10px]'}`}>
          {actionError}
        </p>
      ) : null}
      {pickerPortal}
    </div>
  )
}
