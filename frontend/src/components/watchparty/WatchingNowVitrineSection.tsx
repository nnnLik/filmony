import { Avatar } from '@telegram-apps/telegram-ui'
import { useQuery } from '@tanstack/react-query'
import { Clapperboard } from 'lucide-react'
import { Link } from 'react-router'

import { getFollowingWatchingNow } from '../../api/watchPartyWatchingApi'
import type { FollowingWatchingNowItem } from '../../api/watchPartyTypes'
import { filmWatchPath } from '../../lib/openFilmWatchInBrowser'
import { profileInitials } from '../../lib/profileDisplay'

const followingWatchingNowQueryKey = ['following-watching-now'] as const

function cardInitials(item: FollowingWatchingNowItem): string {
  return profileInitials({
    display_name: item.display_name,
    first_name: null,
    username: item.slug,
  })
}

function WatchingNowCard({ item }: { item: FollowingWatchingNowItem }) {
  const watchHref = filmWatchPath(item.film_id, item.invite_slug)

  return (
    <Link
      to={watchHref}
      className="w-34 shrink-0 overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) no-underline"
      aria-label={`${item.display_name} смотрит «${item.film_title}»`}
    >
      <div className="relative aspect-2/3 w-full">
        {item.film_poster_url ? (
          <img src={item.film_poster_url} alt="" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full min-h-26 items-center justify-center px-1 text-center text-[10px] text-(--tgui--hint_color)">
            Нет постера
          </div>
        )}
        <span className="absolute left-1.5 top-1.5 inline-flex items-center gap-0.5 rounded-md bg-[color-mix(in_srgb,var(--tgui--bg_color)_82%,transparent)] px-1.5 py-0.5 text-[10px] font-medium text-(--tgui--text_color) shadow-sm backdrop-blur-sm">
          <Clapperboard className="size-3 shrink-0" aria-hidden />
          Сейчас
        </span>
        <span className="absolute bottom-1.5 right-1.5">
          <Avatar
            src={item.photo_url ?? undefined}
            acronym={cardInitials(item)}
            size={28}
          />
        </span>
      </div>
      <div className="space-y-1 p-2">
        <p className="line-clamp-2 min-h-10 text-[11px] font-medium leading-snug text-(--tgui--text_color)">
          {item.film_title}
        </p>
        <p className="truncate text-[10px] text-(--tgui--hint_color)">{item.display_name}</p>
      </div>
    </Link>
  )
}

export type WatchingNowVitrineSectionProps = {
  enabled?: boolean
  className?: string
}

export function WatchingNowVitrineSection({
  enabled = true,
  className = '',
}: WatchingNowVitrineSectionProps) {
  const query = useQuery({
    queryKey: followingWatchingNowQueryKey,
    queryFn: () => getFollowingWatchingNow(),
    enabled,
    staleTime: 60_000,
    refetchInterval: 60_000,
  })

  const items = query.data?.items ?? []
  if (!enabled || items.length === 0) {
    return null
  }

  return (
    <section className={className}>
      <p className="mb-2 px-1 text-sm font-semibold text-(--tgui--text_color)">
        Сейчас смотрят друзья
      </p>
      <div className="flex gap-2.5 overflow-x-auto overflow-y-hidden pb-1 pl-1 pr-1 pt-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {items.map((item) => (
          <WatchingNowCard key={item.user_id} item={item} />
        ))}
      </div>
    </section>
  )
}
