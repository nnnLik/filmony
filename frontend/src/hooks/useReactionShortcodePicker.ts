import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEventHandler,
  type RefObject,
} from 'react'

import type { ReactionCatalogItem } from '../api/profileTypes'
import { reactionTokenFromShortcode } from '../lib/commentReactionTokens'
import {
  filterCatalogItemsForShortcodeQuery,
  flattenReactionCatalogItems,
  parseActiveShortcodeQuery,
  type ActiveShortcodeQuery,
} from '../lib/commentShortcodeCompose'
import { loadReactionCatalog } from '../lib/reactionCatalogCache'
import { applyMentionPick } from '../lib/feedMentionCompose'
import { useMentionPopoverLayout } from '../lib/useMentionPopoverLayout'

type CaretField = {
  selectionStart: number | null
  focus: () => void
  setSelectionRange: HTMLTextAreaElement['setSelectionRange']
}

export type UseReactionShortcodePickerArgs = {
  enabled?: boolean
  value: string
  fieldRef: { readonly current: CaretField | null }
  maxLen?: number
  onApply: (nextValue: string, caret: number) => void
  dismissMention?: () => void
}

export type UseReactionShortcodePickerResult = {
  anchorRef: RefObject<HTMLDivElement | null>
  picker: ActiveShortcodeQuery | null
  highlightIdx: number
  filtered: ReactionCatalogItem[]
  popoverLayout: ReturnType<typeof useMentionPopoverLayout>
  syncFromValue: (value: string, caretOverride?: number | null) => void
  pick: (item: ReactionCatalogItem) => void
  dismiss: () => void
  handleKeyDown: KeyboardEventHandler<HTMLTextAreaElement | HTMLInputElement>
  catalogPending: boolean
}

export function useReactionShortcodePicker({
  enabled = true,
  value,
  fieldRef,
  maxLen,
  onApply,
  dismissMention,
}: UseReactionShortcodePickerArgs): UseReactionShortcodePickerResult {
  const [picker, setPicker] = useState<ActiveShortcodeQuery | null>(null)
  const [highlightIdx, setHighlightIdx] = useState(0)
  const [catalogItems, setCatalogItems] = useState<ReactionCatalogItem[]>([])
  const [catalogPending, setCatalogPending] = useState(false)
  const anchorRef = useRef<HTMLDivElement>(null)

  const pickerOpen = picker != null && enabled

  const filtered = useMemo(
    () =>
      pickerOpen && picker != null
        ? filterCatalogItemsForShortcodeQuery(catalogItems, picker.query)
        : [],
    [catalogItems, picker, pickerOpen],
  )

  const highlightSafe = useMemo(() => {
    if (filtered.length === 0) return 0
    return Math.min(highlightIdx, filtered.length - 1)
  }, [filtered.length, highlightIdx])

  const popoverLayout = useMentionPopoverLayout(pickerOpen, anchorRef)

  const dismiss = useCallback(() => {
    setPicker(null)
    setHighlightIdx(0)
    setCatalogPending(false)
  }, [])

  const syncFromValue = useCallback(
    (nextValue: string, caretOverride?: number | null) => {
      if (!enabled) {
        dismiss()
        return
      }
      const el = fieldRef.current
      const caret =
        caretOverride != null
          ? Math.min(Math.max(0, caretOverride), nextValue.length)
          : Math.min(el?.selectionStart ?? nextValue.length, nextValue.length)
      const active = parseActiveShortcodeQuery(nextValue, caret)
      if (active == null) {
        dismiss()
        return
      }
      dismissMention?.()
      if (picker == null) {
        setCatalogPending(true)
      }
      setPicker(active)
      setHighlightIdx(0)
    },
    [dismiss, dismissMention, enabled, fieldRef, picker],
  )

  useEffect(() => {
    if (!pickerOpen) {
      return
    }
    let alive = true
    void loadReactionCatalog()
      .then((catalog) => {
        if (!alive) return
        const items = flattenReactionCatalogItems(catalog)
        queueMicrotask(() => {
          if (!alive) return
          setCatalogItems(items)
          setCatalogPending(false)
        })
      })
      .catch(() => {
        if (!alive) return
        queueMicrotask(() => {
          if (!alive) return
          setCatalogItems([])
          setCatalogPending(false)
        })
      })
    return () => {
      alive = false
    }
  }, [pickerOpen])

  const pick = useCallback(
    (item: ReactionCatalogItem) => {
      if (picker == null) return
      const endCaret = picker.colonIndex + 1 + picker.query.length
      const caret = Math.min(endCaret, value.length)
      const token = reactionTokenFromShortcode(item.shortcode)
      const res = applyMentionPick(value, caret, picker.colonIndex, token, maxLen)
      if (res == null) return
      dismiss()
      onApply(res.nextValue, res.caret)
    },
    [dismiss, maxLen, onApply, picker, value],
  )

  const handleKeyDown: KeyboardEventHandler<HTMLTextAreaElement | HTMLInputElement> = useCallback(
    (event) => {
      if (picker == null || !enabled) return
      if (event.key === 'ArrowDown') {
        event.preventDefault()
        setHighlightIdx((index) => {
          const max = Math.max(0, filtered.length - 1)
          return Math.min(max, index + 1)
        })
      } else if (event.key === 'ArrowUp') {
        event.preventDefault()
        setHighlightIdx((index) => Math.max(0, index - 1))
      } else if (event.key === 'Enter' && filtered.length > 0) {
        event.preventDefault()
        const row = filtered[highlightSafe] ?? filtered[0]
        if (row != null) {
          pick(row)
        }
      }
    },
    [enabled, filtered, highlightSafe, pick, picker],
  )

  return {
    anchorRef,
    picker: pickerOpen ? picker : null,
    highlightIdx: highlightSafe,
    filtered,
    popoverLayout,
    syncFromValue,
    pick,
    dismiss,
    handleKeyDown,
    catalogPending,
  }
}
