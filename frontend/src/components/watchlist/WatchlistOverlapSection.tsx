import { Avatar, Button } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { Users } from 'lucide-react'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { getMyWatchlistOverlaps } from '../../api/watchlistApi'
import type { WatchlistOverlapItem } from '../../api/profileTypes'
import {
  buildWatchlistNewHref,
  findWatchlistOverlapForAnchor,
  type WatchlistOverlapAnchor,
} from '../../lib/watchlistOverlapUtils'
import type { WatchlistOverlapPartner } from '../../api/profileTypes'
import { profileInitials } from '../../lib/profileDisplay'

function partnerDisplayName(partner: WatchlistOverlapPartner): string {
  if (partner.display_name?.trim()) {
    return partner.display_name.trim()
  }
  if (partner.slug?.trim()) {
    return `@${partner.slug.trim()}`
  }
  return 'Пользователь'
}

function partnerInitials(partner: WatchlistOverlapPartner): string {
  return profileInitials({
    display_name: partner.display_name,
    first_name: null,
    username: partner.slug,
  })
}

export type WatchlistOverlapSectionProps = {
  enabled?: boolean
}

function OverlapCard({ item, onWatchTogether }: { item: WatchlistOverlapItem; onWatchTogether: () => void }) {
  const partnerPreview = item.partners.slice(0, 3)
  const extraCount = Math.max(0, item.partners.length - partnerPreview.length)

  return (
    <div className="w-34 shrink-0 overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
      <div className="relative aspect-2/3 w-full">
        {item.poster_url ? (
          <img src={item.poster_url} alt={item.title} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full min-h-26 items-center justify-center px-1 text-center text-[10px] text-(--tgui--hint_color)">
            Нет постера
          </div>
        )}
        <span className="absolute bottom-1.5 left-1.5 flex items-center gap-0.5 rounded-md bg-[color-mix(in_srgb,var(--tgui--bg_color)_82%,transparent)] px-1.5 py-0.5 text-[10px] font-medium text-(--tgui--text_color) shadow-sm backdrop-blur-sm">
          <Users className="block" size={11} strokeWidth={2} aria-hidden />
          {item.partners.length}
        </span>
      </div>
      <div className="space-y-2 p-2">
        <p className="line-clamp-2 min-h-10 text-[11px] font-medium leading-snug text-(--tgui--text_color)">
          {item.title}
        </p>
        {partnerPreview.length > 0 ? (
          <div className="flex items-center gap-1">
            {partnerPreview.map((partner) => (
              <Avatar
                key={partner.user_id}
                src={partner.avatar_url ?? undefined}
                acronym={partnerInitials(partner)}
                size={24}
              />
            ))}
            {extraCount > 0 ? (
              <span className="text-[10px] font-medium text-(--tgui--hint_color)">+{extraCount}</span>
            ) : null}
          </div>
        ) : null}
        <Button size="s" stretched onClick={onWatchTogether}>
          Смотрим вместе
        </Button>
      </div>
    </div>
  )
}

export function WatchlistOverlapSection({ enabled = true }: WatchlistOverlapSectionProps) {
  const navigate = useNavigate()
  const overlapsQuery = useQuery({
    queryKey: ['watchlistOverlaps'],
    queryFn: () => getMyWatchlistOverlaps({ limit: 20 }),
    enabled,
    staleTime: 60_000,
    gcTime: 10 * 60_000,
  })

  const items = overlapsQuery.data?.items ?? []
  if (!enabled || overlapsQuery.isLoading || items.length === 0) {
    return null
  }

  return (
    <div className="mb-5">
      <p className="mb-2 px-1 text-sm font-semibold text-(--tgui--text_color)">Ещё хотят посмотреть</p>
      <div className="flex gap-2.5 overflow-x-auto overflow-y-hidden pb-1 pl-1 pr-1 pt-0.5 [-ms-overflow-style:none] scrollbar-none [&::-webkit-scrollbar]:hidden">
        {items.map((item) => (
          <OverlapCard
            key={item.card_id}
            item={item}
            onWatchTogether={() => {
              void navigate(buildWatchlistNewHref(item))
            }}
          />
        ))}
      </div>
    </div>
  )
}

export type WatchlistOverlapAnchorBannerProps = {
  anchor: WatchlistOverlapAnchor | null
  enabled?: boolean
  inViewerWatchlist?: boolean | null
  onWatchTogether?: () => void
}

export function WatchlistOverlapAnchorBanner({
  anchor,
  enabled = true,
  inViewerWatchlist = null,
  onWatchTogether,
}: WatchlistOverlapAnchorBannerProps) {
  const navigate = useNavigate()
  const overlapsQuery = useQuery({
    queryKey: ['watchlistOverlaps'],
    queryFn: () => getMyWatchlistOverlaps({ limit: 50 }),
    enabled: enabled && anchor != null,
    staleTime: 60_000,
    gcTime: 10 * 60_000,
  })

  const overlap = useMemo(() => {
    if (anchor == null || overlapsQuery.data == null) {
      return null
    }
    return findWatchlistOverlapForAnchor(overlapsQuery.data.items, anchor)
  }, [anchor, overlapsQuery.data])

  if (!enabled || anchor == null || overlapsQuery.isLoading || overlap == null || overlap.partners.length === 0) {
    return null
  }

  const partnerCount = overlap.partners.length
  const label =
    partnerCount === 1
      ? 'Ещё у 1 в «Позже»'
      : `Ещё у ${partnerCount} в «Позже»`

  const handleWatchTogether = () => {
    if (onWatchTogether != null) {
      onWatchTogether()
      return
    }
    void navigate(buildWatchlistNewHref(overlap))
  }

  return (
    <div className="rounded-xl border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_22%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_8%,var(--tgui--secondary_bg_color))] p-3">
      <div className="flex items-start gap-2.5">
        <div className="flex -space-x-2 pt-0.5">
          {overlap.partners.slice(0, 4).map((partner) => (
            <Avatar
              key={partner.user_id}
              src={partner.avatar_url ?? undefined}
              acronym={partnerInitials(partner)}
              size={28}
            />
          ))}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-(--tgui--text_color)">{label}</p>
          <p className="mt-0.5 line-clamp-2 text-xs text-(--tgui--hint_color)">
            {overlap.partners.map((p) => partnerDisplayName(p)).join(', ')}
          </p>
        </div>
      </div>
      {inViewerWatchlist === false ? (
        <Button size="s" stretched className="mt-3!" onClick={handleWatchTogether}>
          Смотрим вместе
        </Button>
      ) : null}
    </div>
  )
}

