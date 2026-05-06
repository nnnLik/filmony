import { useCallback, useEffect, useLayoutEffect, useState, type CSSProperties, type RefObject } from 'react'

import { POPOVER_GAP, SIDE_PAD } from './constants'

export function usePopoverPosition(
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
