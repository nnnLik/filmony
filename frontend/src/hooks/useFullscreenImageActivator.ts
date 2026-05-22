import {
  createElement,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent as ReactMouseEvent,
  type ReactElement,
  type TouchEvent as ReactTouchEvent,
} from 'react'

import { FullscreenImageOverlay } from '../components/media/FullscreenImageOverlay'

const DEFAULT_NAV_DELAY_MS = 280
const DOUBLE_TAP_MS = 330

export type UseFullscreenImageActivatorOptions = {
  /** When false, handlers are no-ops */
  enabled: boolean
  /** Image URL for fullscreen; empty enables navigation-only bindings when `onSingleNavigate` exists */
  imageSrc: string | null | undefined
  imageAlt?: string
  onSingleNavigate?: (() => void) | null
  navigateDelayMs?: number
}

export type FullscreenActivatorBindings = {
  onClickCapture: (e: React.MouseEvent<Element>) => void
  onTouchEndCapture: (e: ReactTouchEvent<Element>) => void
  onTouchMoveCapture: (e: ReactTouchEvent<Element>) => void
  onKeyDown: (e: ReactKeyboardEvent<Element>) => void
}

/**
 * Fullscreen viewer on mouse `detail>=2` / touch double-tap when an image URL is present.
 * When `onSingleNavigate` is passed, plain activations defer navigation so double-open can cancel it.
 */
export function useFullscreenImageActivator({
  enabled,
  imageSrc,
  imageAlt = '',
  onSingleNavigate,
  navigateDelayMs = DEFAULT_NAV_DELAY_MS,
}: UseFullscreenImageActivatorOptions) {
  const [viewerOpen, setViewerOpen] = useState(false)
  const resolvedSrc = typeof imageSrc === 'string' ? imageSrc.trim() : ''
  const canOpenFullscreen = resolvedSrc !== ''
  const navFn = typeof onSingleNavigate === 'function' ? onSingleNavigate : null

  const navTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const lastTouchEndTsRef = useRef(0)
  const suppressClickRef = useRef(false)
  const touchMovedRef = useRef(false)

  const clearNavTimer = useCallback(() => {
    if (navTimerRef.current != null) {
      clearTimeout(navTimerRef.current)
      navTimerRef.current = null
    }
  }, [])

  const openViewer = useCallback(() => {
    if (!canOpenFullscreen) return
    clearNavTimer()
    setViewerOpen(true)
  }, [canOpenFullscreen, clearNavTimer])

  const closeViewer = useCallback(() => {
    setViewerOpen(false)
  }, [])

  useEffect(() => {
    return () => {
      clearNavTimer()
    }
  }, [clearNavTimer])

  const bindings = useMemo((): FullscreenActivatorBindings => {
    const scheduleNavigate = (): void => {
      if (navFn == null) return
      clearNavTimer()
      suppressClickRef.current = true
      navTimerRef.current = setTimeout(() => {
        navTimerRef.current = null
        suppressClickRef.current = false
        navFn()
      }, navigateDelayMs)
    }

    return {
      onClickCapture: (e: ReactMouseEvent<Element>) => {
        if (!enabled) return
        const isTouchSynth = ((): boolean => {
          const native = e.nativeEvent
          if ('pointerType' in native && typeof native.pointerType === 'string') {
            return native.pointerType === 'touch'
          }
          return false
        })()

        if (suppressClickRef.current) {
          suppressClickRef.current = false
          if (canOpenFullscreen) {
            e.preventDefault()
            e.stopPropagation()
          }
          return
        }

        if (!canOpenFullscreen) {
          if (navFn == null) return
          if (isTouchSynth) return
          if (touchMovedRef.current) {
            touchMovedRef.current = false
            return
          }
          if (e.detail === 1) {
            e.preventDefault()
            e.stopPropagation()
            scheduleNavigate()
          }
          return
        }

        if (isTouchSynth) {
          if (touchMovedRef.current) {
            touchMovedRef.current = false
            return
          }
          // Touch sequencing is driven from `touchend`.
          if (navFn != null) {
            e.preventDefault()
            e.stopPropagation()
          }
          return
        }

        clearNavTimer()
        if (navFn == null) {
          if (e.detail >= 2) {
            e.preventDefault()
            e.stopPropagation()
            openViewer()
          }
          return
        }

        if (e.detail === 1) {
          e.preventDefault()
          e.stopPropagation()
          navTimerRef.current = setTimeout(() => {
            navTimerRef.current = null
            navFn()
          }, navigateDelayMs)
          return
        }
        if (e.detail >= 2) {
          e.preventDefault()
          e.stopPropagation()
          openViewer()
        }
      },
      onTouchEndCapture: (e: ReactTouchEvent<Element>) => {
        if (!enabled) return
        clearNavTimer()
        const now = Date.now()
        const moved = touchMovedRef.current
        touchMovedRef.current = false
        const prevTap = lastTouchEndTsRef.current
        const isDoubleTap = canOpenFullscreen && !moved && prevTap > 0 && now - prevTap < DOUBLE_TAP_MS

        if (isDoubleTap) {
          lastTouchEndTsRef.current = 0
          e.preventDefault()
          e.stopPropagation()
          suppressClickRef.current = true
          openViewer()
          return
        }

        lastTouchEndTsRef.current = moved ? 0 : now
        if (moved || navFn == null) return

        if (!canOpenFullscreen) {
          e.preventDefault()
          e.stopPropagation()
          scheduleNavigate()
          return
        }

        e.preventDefault()
        e.stopPropagation()
        scheduleNavigate()
      },
      onTouchMoveCapture: () => {
        touchMovedRef.current = true
      },
      onKeyDown: (e: ReactKeyboardEvent<Element>) => {
        if (navFn == null) return
        if (e.key !== 'Enter' && e.key !== ' ') return
        e.preventDefault()
        navFn()
      },
    }
  }, [enabled, canOpenFullscreen, navigateDelayMs, navFn, clearNavTimer, openViewer])

  const overlay: ReactElement | null =
    viewerOpen && canOpenFullscreen
      ? createElement(FullscreenImageOverlay, {
          open: true,
          alt: imageAlt,
          src: resolvedSrc,
          onClose: closeViewer,
        })
      : null

  return {
    overlay,
    openViewer,
    closeViewer,
    bindings,
    canOpenFullscreen,
  }
}
