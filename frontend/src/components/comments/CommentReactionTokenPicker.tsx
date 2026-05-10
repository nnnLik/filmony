import { IconButton } from '@telegram-apps/telegram-ui'
import { Smile } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState, type MouseEvent } from 'react'
import { createPortal } from 'react-dom'

import { ApiError, formatApiDetail } from '../../api/client'
import type { ReactionCatalogTab, ReactionGroupedCatalog } from '../../api/profileTypes'
import { clearReactionCatalogCache, loadReactionCatalog } from '../../lib/reactionCatalogCache'
import { ReactionStripPopover } from '../reactions/reactionStrip/ReactionStripPopover'
import { POPOVER_W_COMPACT } from '../reactions/reactionStrip/constants'
import { usePopoverPosition } from '../reactions/reactionStrip/usePopoverPosition'

export type CommentReactionTokenPickerProps = {
  onPickReactionTypeId: (reactionTypeId: number) => void
  disabled?: boolean
  /** When false, picker does not open (e.g. at max length). */
  allowInsert?: boolean
}

export function CommentReactionTokenPicker({
  onPickReactionTypeId,
  disabled = false,
  allowInsert = true,
}: CommentReactionTokenPickerProps) {
  const [pickerOpen, setPickerOpen] = useState(false)
  const [catalog, setCatalog] = useState<ReactionGroupedCatalog | null>(null)
  const [catalogError, setCatalogError] = useState<string | null>(null)
  const [activeTabSlug, setActiveTabSlug] = useState<string | null>(null)

  const triggerRef = useRef<HTMLButtonElement>(null)
  const { style: popoverStyle, placeAbove } = usePopoverPosition(triggerRef, pickerOpen, POPOVER_W_COMPACT)

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
  const recentItems = catalog?.recent ?? []

  const apply = useCallback(
    (reactionTypeId: number) => {
      onPickReactionTypeId(reactionTypeId)
      clearReactionCatalogCache()
      closePicker()
    },
    [closePicker, onPickReactionTypeId],
  )

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
        busy={false}
        effectiveTabSlug={effectiveTabSlug}
        onTabSelect={setActiveTabSlug}
        compact
        contentDensity="dense"
        myReactionIds={new Set()}
        countsById={new Map()}
        apply={apply}
        recentItems={recentItems}
        gridItems={gridItems}
        activeTab={activeTab}
      />,
      document.body,
    )

  const blocked = disabled || !allowInsert

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
          setPickerOpen((wasOpen) => {
            if (wasOpen) return false
            setCatalog(null)
            setCatalogError(null)
            return true
          })
        }}
        aria-expanded={pickerOpen}
        aria-label="Вставить реакцию в комментарий"
        className="relative z-0 box-border! flex! h-8! w-8! min-h-8! min-w-8! shrink-0 items-center! justify-center! rounded-full p-0! leading-none! text-(--tgui--hint_color)"
      >
        <Smile className="relative z-1 block size-[18px] shrink-0" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" aria-hidden />
      </IconButton>
      {pickerPortal}
    </>
  )
}
