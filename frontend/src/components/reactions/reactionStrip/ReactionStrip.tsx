import { IconButton } from '@telegram-apps/telegram-ui'
import { Smile } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState, type MouseEvent } from 'react'
import { createPortal } from 'react-dom'

import { ApiError, formatApiDetail } from '../../../api/client'
import type {
  ReactionCatalogTab,
  ReactionGroupedCatalog,
  ReactionCountItem,
  ReactionSummary,
} from '../../../api/profileTypes'
import { setUserReaction } from '../../../api/reactionApi'
import { loadReactionCatalog } from '../../../lib/reactionCatalogCache'
import {
  readRecentReactionTypeIds,
  recordRecentReactionTypeId,
  resolveRecentCatalogItems,
} from '../../../lib/localRecentReactions'
import { CountPill } from './CountPill'
import {
  EMPTY,
  POPOVER_W_COMPACT,
  POPOVER_W_DEFAULT,
} from './constants'
import { ReactionStripPopover } from './ReactionStripPopover'
import { usePopoverPosition } from './usePopoverPosition'

export type ReactionStripProps = {
  targetKind: 'movie_card' | 'movie_card_comment'
  targetId: number
  summary: ReactionSummary | undefined
  onSummaryChange: (next: ReactionSummary) => void
  className?: string
  /** Один узкий ряд под текстом комментария (крупнее кружки‑реакции). */
  compact?: boolean
  /** Ещё чуть компактнее пиллы и попап (шапка страницы карточки). */
  compactTight?: boolean
}

export function ReactionStrip({
  targetKind,
  targetId,
  summary,
  onSummaryChange,
  className,
  compact = false,
  compactTight = false,
}: ReactionStripProps) {
  const effective = summary ?? EMPTY
  const myReactionIds = useMemo(
    () => new Set(effective.my_reaction_type_ids),
    [effective.my_reaction_type_ids],
  )
  const pillTight = compact && compactTight
  const popoverDense = pillTight
  const popoverW = compact ? POPOVER_W_COMPACT : POPOVER_W_DEFAULT
  const [pickerOpen, setPickerOpen] = useState(false)
  const [catalog, setCatalog] = useState<ReactionGroupedCatalog | null>(null)
  const [catalogError, setCatalogError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [activeTabSlug, setActiveTabSlug] = useState<string | null>(null)
  const [recentRevision, setRecentRevision] = useState(0)

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

  const activeTab = useMemo((): ReactionCatalogTab | null => {
    if (!catalog || !effectiveTabSlug) return null
    return catalog.tabs.find((t) => t.category_slug === effectiveTabSlug) ?? null
  }, [catalog, effectiveTabSlug])

  const gridItems = activeTab?.items ?? []
  const recentItems = useMemo(() => {
    void recentRevision
    return resolveRecentCatalogItems(catalog, readRecentReactionTypeIds())
  }, [catalog, recentRevision])

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
        recordRecentReactionTypeId(reactionTypeId)
        setRecentRevision((n) => n + 1)
        closePicker()
      } catch (e) {
        setActionError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Не удалось применить')
      } finally {
        setBusy(false)
      }
    },
    [closePicker, onSummaryChange, targetId, targetKind],
  )

  const countsById = useMemo(() => {
    const m = new Map<number, ReactionCountItem>()
    effective.counts.forEach((c) => m.set(c.reaction_type_id, c))
    return m
  }, [effective])

  const pickerPortal =
    pickerOpen &&
    popoverStyle &&
    typeof document !== 'undefined' &&
    createPortal(
      <ReactionStripPopover
        closePicker={closePicker}
        popoverStyle={popoverStyle}
        placeAbove={placeAbove}
        catalogError={catalogError}
        catalog={catalog}
        busy={busy}
        effectiveTabSlug={effectiveTabSlug}
        onTabSelect={setActiveTabSlug}
        compact={compact}
        contentDensity={popoverDense ? 'dense' : 'default'}
        myReactionIds={myReactionIds}
        countsById={countsById}
        apply={(id) => {
          void apply(id)
        }}
        recentItems={recentItems}
        gridItems={gridItems}
        activeTab={activeTab}
      />,
      document.body,
    )

  return (
    <div className={compact ? `${className ?? ''} min-w-0 flex-1` : className}>
      <div
        className={
          compact
            ? `${pillTight ? 'flex min-h-9 pb-0' : 'flex min-h-10 pb-px'} w-full max-w-full min-w-0 flex-nowrap items-center gap-x-1 gap-y-0 overflow-x-auto [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden`
            : 'flex flex-wrap items-center gap-1'
        }
      >
        {effective.counts.map((c) => {
          const mine = myReactionIds.has(c.reaction_type_id)
          return (
            <CountPill
              key={c.reaction_type_id}
              disabled={busy}
              mine={mine}
              imageUrl={c.image_url}
              count={c.count}
              reactors={c.reactors ?? []}
              compact={compact}
              pillTight={pillTight}
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
            compact && pillTight
              ? 'relative z-0 box-border! flex! h-10! w-10! min-h-10! min-w-10! shrink-0 items-center! justify-center! rounded-full p-0! leading-none! text-(--tgui--hint_color) transition-[transform,colors] hover:text-(--tgui--text_color) active:scale-[0.97] aria-expanded:text-(--tgui--link_color)!'
              : compact
                ? 'relative z-0 box-border! flex! h-11! w-11! min-h-11! min-w-11! shrink-0 items-center! justify-center! rounded-full p-0! leading-none! text-(--tgui--hint_color) transition-[transform,colors] hover:text-(--tgui--text_color) active:scale-[0.97] aria-expanded:text-(--tgui--link_color)!'
                : 'relative z-0 box-border! flex! h-9! w-9! min-h-9! min-w-9! shrink-0 items-center! justify-center! rounded-full p-0! leading-none! text-(--tgui--hint_color) transition-[transform,colors] hover:text-(--tgui--text_color) active:scale-[0.98] aria-expanded:text-(--tgui--link_color)!'
          }
        >
          <Smile
            className={`relative z-1 block shrink-0 ${compact && pillTight ? 'size-[22px]' : compact ? 'size-[26px]' : 'size-[18px]'}`}
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
