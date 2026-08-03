import { useEffect } from 'react'

import { PEPE_DANCING_GIF_URL } from '../../lib/pepeGif'

type PepeExtremeRatingBubbleProps = {
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

export function PepeExtremeRatingBubble({
  message,
  onDismiss,
  durationMs = 3200,
}: PepeExtremeRatingBubbleProps) {
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
      className={`mt-3 flex items-start gap-3 rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)] px-3 py-2.5 text-left shadow-sm ${
        reduceMotion ? '' : 'motion-safe:animate-[filmony-detail-fade-in_0.2s_ease-out_both]'
      }`}
    >
      {!reduceMotion ? (
        <img
          src={PEPE_DANCING_GIF_URL}
          alt=""
          aria-hidden
          className="size-10 shrink-0 rounded-xl object-cover"
          loading="lazy"
          decoding="async"
        />
      ) : null}
      <p className="min-w-0 flex-1 text-sm leading-snug text-(--tgui--text_color)">{message}</p>
    </div>
  )
}
