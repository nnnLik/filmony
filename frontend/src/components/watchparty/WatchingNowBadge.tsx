import { useState } from 'react'
import { Clapperboard } from 'lucide-react'

import type { WatchingNowBatchItem } from '../../api/watchPartyTypes'

export type WatchingNowBadgeProps = {
  item: WatchingNowBatchItem
  className?: string
}

export function WatchingNowBadge({ item, className = '' }: WatchingNowBadgeProps) {
  const [open, setOpen] = useState(false)
  const title = item.film_title.trim()

  if (title === '') {
    return null
  }

  const truncated = title.length > 18 ? `${title.slice(0, 17)}…` : title

  return (
    <span
      className={`relative inline-flex ${className}`}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className="inline-flex max-w-[9rem] items-center gap-1 rounded-full bg-white/10 px-2 py-0.5 text-[11px] font-medium text-(--tgui--text_color)"
        aria-label={`Сейчас смотрит: ${title}`}
        onClick={(e) => {
          e.stopPropagation()
          e.preventDefault()
          setOpen((v) => !v)
        }}
      >
        <Clapperboard className="size-3 shrink-0" aria-hidden />
        <span className="truncate">{truncated}</span>
      </button>
      {open ? (
        <span
          role="tooltip"
          className="absolute left-0 top-full z-30 mt-1 min-w-[10rem] rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-2 text-left shadow-lg"
          onClick={(e) => e.stopPropagation()}
        >
          <p className="text-xs text-(--tgui--hint_color)">Сейчас смотрит</p>
          <p className="mt-0.5 text-sm text-(--tgui--text_color)">{title}</p>
        </span>
      ) : null}
    </span>
  )
}

export type WatchingNowAuthorBadgeProps = {
  watchingByUserId: Record<string, WatchingNowBatchItem>
  authorId: string
  className?: string
}

export function WatchingNowAuthorBadge({
  watchingByUserId,
  authorId,
  className,
}: WatchingNowAuthorBadgeProps) {
  const item = watchingByUserId[authorId]
  if (item == null) {
    return null
  }
  return <WatchingNowBadge item={item} className={className} />
}
