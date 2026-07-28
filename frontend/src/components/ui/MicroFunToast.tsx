import { useEffect } from 'react'

type MicroFunToastProps = {
  message: string | null
  onDismiss: () => void
  durationMs?: number
}

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') {
    return false
  }
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function MicroFunToast({ message, onDismiss, durationMs = 3000 }: MicroFunToastProps) {
  const reduceMotion = prefersReducedMotion()

  useEffect(() => {
    if (message == null) {
      return undefined
    }
    const timer = window.setTimeout(() => {
      onDismiss()
    }, durationMs)
    return () => {
      window.clearTimeout(timer)
    }
  }, [message, durationMs, onDismiss])

  if (message == null) {
    return null
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className={`pointer-events-none fixed inset-x-4 z-300 mx-auto max-w-md rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)] px-4 py-3 text-center text-sm text-(--tgui--text_color) shadow-lg backdrop-blur-md ${reduceMotion ? '' : 'motion-safe:animate-[filmony-detail-fade-in_0.2s_ease-out_both]'}`}
      style={{ bottom: 'calc(4.75rem + env(safe-area-inset-bottom, 0px))' }}
    >
      {message}
    </div>
  )
}
