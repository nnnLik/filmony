import { Users } from 'lucide-react'
import { Link } from 'react-router-dom'

import type { WatchlistEntryItem } from '../../api/profileTypes'

type WatchlistPosterGridProps = {
  items: WatchlistEntryItem[]
}

function watchlistNewHref(item: WatchlistEntryItem): string {
  const params = new URLSearchParams()
  if (item.provider === 'kinopoisk' && item.film_id != null && item.film_id > 0) {
    params.set('filmId', String(item.film_id))
    return `/watchlist/new?${params.toString()}`
  }
  if (item.catalog_item_id != null && item.catalog_item_id > 0) {
    params.set('catalogItemId', String(item.catalog_item_id))
    return `/watchlist/new?${params.toString()}`
  }
  if (item.card_id.trim() !== '') {
    params.set('watchlistCardId', item.card_id)
  }
  return `/watchlist/new?${params.toString()}`
}

function watchlistItemHref(item: WatchlistEntryItem): string | null {
  const plannedId = item.planned_user_card_id
  if (plannedId != null && plannedId > 0) {
    return `/cards/${plannedId}`
  }
  if (item.provider === 'kinopoisk' && item.film_id != null && item.film_id > 0) {
    return watchlistNewHref(item)
  }
  if (item.catalog_item_id != null && item.catalog_item_id > 0) {
    return watchlistNewHref(item)
  }
  if (item.card_id.trim() !== '') {
    return watchlistNewHref(item)
  }
  return null
}

function watchlistItemTitle(item: WatchlistEntryItem): string {
  return item.title || item.film_title || 'Untitled'
}

function watchlistItemPoster(item: WatchlistEntryItem): string | null {
  return item.poster_url ?? item.film_poster_url ?? null
}

function WatchlistPosterCell({ item }: { item: WatchlistEntryItem }) {
  const title = watchlistItemTitle(item)
  const poster = watchlistItemPoster(item)
  const href = watchlistItemHref(item)
  const hasWatchWith =
    (item.watch_with_user_ids != null && item.watch_with_user_ids.length > 0) ||
    (item.watch_with_user_id != null && item.watch_with_user_id !== '')

  const badge = hasWatchWith ? (
    <span
      className="absolute bottom-1.5 left-1.5 flex items-center gap-0.5 rounded-md bg-[color-mix(in_srgb,var(--tgui--bg_color)_82%,transparent)] px-1.5 py-0.5 text-[10px] font-medium text-(--tgui--text_color) shadow-sm backdrop-blur-sm"
      title="Смотреть вместе"
    >
      <Users className="block" size={11} strokeWidth={2} aria-hidden />
      Вместе
    </span>
  ) : null

  const inner = (
    <div className="relative aspect-2/3 w-full">
      {poster ? (
        <img src={poster} alt={title} className="h-full w-full object-cover" />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-[11px] text-(--tgui--hint_color)">
          Нет постера
        </div>
      )}
      {badge}
    </div>
  )

  const shellClass =
    'relative block overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)'

  if (href == null) {
    return (
      <div className={shellClass} aria-label={`«${title}» в списке «Позже»`}>
        {inner}
      </div>
    )
  }

  return (
    <Link to={href} className={`${shellClass} no-underline`} aria-label={`Открыть «${title}»`}>
      {inner}
    </Link>
  )
}

export function WatchlistPosterGrid({ items }: WatchlistPosterGridProps) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {items.map((item) => (
        <WatchlistPosterCell key={item.entry_id} item={item} />
      ))}
    </div>
  )
}
