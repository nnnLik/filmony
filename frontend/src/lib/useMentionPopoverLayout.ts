import { useCallback, useLayoutEffect, useState, type RefObject } from 'react'

export type MentionPopoverLayout = {
  top: number
  left: number
  width: number
  maxHeight: number
}

const VIEW_MARGIN = 8
const GAP = 6
const MIN_HEIGHT = 96

/**
 * Measures anchor rect in viewport and returns fixed coordinates for a mention list
 * so it is not clipped by scroll/overflow ancestors (bottom sheets, panels).
 */
export function useMentionPopoverLayout(
  open: boolean,
  anchorRef: RefObject<HTMLElement | null>,
): MentionPopoverLayout | null {
  const [layout, setLayout] = useState<MentionPopoverLayout | null>(null)

  const measure = useCallback(() => {
    if (!open) {
      setLayout(null)
      return
    }
    const el = anchorRef.current
    if (el == null) {
      setLayout(null)
      return
    }
    const rect = el.getBoundingClientRect()
    const preferredMax = Math.min(window.innerHeight * 0.4, 224)
    const spaceBelow = window.innerHeight - rect.bottom - GAP - VIEW_MARGIN
    const spaceAbove = rect.top - GAP - VIEW_MARGIN
    const pickBelow = spaceBelow >= MIN_HEIGHT || spaceBelow >= spaceAbove

    const width = Math.min(rect.width, window.innerWidth - VIEW_MARGIN * 2)
    const left = Math.min(Math.max(VIEW_MARGIN, rect.left), window.innerWidth - width - VIEW_MARGIN)

    if (pickBelow) {
      setLayout({
        top: rect.bottom + GAP,
        left,
        width,
        maxHeight: Math.max(MIN_HEIGHT, Math.min(preferredMax, spaceBelow)),
      })
    } else {
      const maxH = Math.max(MIN_HEIGHT, Math.min(preferredMax, spaceAbove))
      const top = rect.top - GAP - maxH
      setLayout({
        top: Math.max(VIEW_MARGIN, top),
        left,
        width,
        maxHeight: maxH,
      })
    }
  }, [open, anchorRef])

  useLayoutEffect(() => {
    if (!open) {
      setLayout(null)
      return
    }
    measure()
    const el = anchorRef.current
    const ro = new ResizeObserver(() => measure())
    if (el != null) {
      ro.observe(el)
    }
    window.addEventListener('resize', measure)
    window.addEventListener('scroll', measure, true)
    return () => {
      ro.disconnect()
      window.removeEventListener('resize', measure)
      window.removeEventListener('scroll', measure, true)
    }
  }, [open, measure])

  if (!open) {
    return null
  }
  return layout
}
