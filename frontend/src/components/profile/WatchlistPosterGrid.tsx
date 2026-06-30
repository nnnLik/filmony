import { Link } from 'react-router-dom'

import type { WatchlistEntryItem } from '../../api/profileTypes'

type WatchlistPosterGridProps = {
  items: WatchlistEntryItem[]
}

function watchlistItemHref(item: WatchlistEntryItem): string | null {
  if (item.provider === 'kinopoisk' && item.film_id != null && item.film_id > 0) {
    return `/films/${encodeURIComponent(String(item.film_id))}`
  }
  if (item.provider === 'rawg' && item.catalog_item_id != null && item.catalog_item_id > 0) {
    return '/cards/new'
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
  const inner = (
    <div className="aspect-2/3 w-full">
      {poster ? (
        <img src={poster} alt={title} className="h-full w-full object-cover" />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-[11px] text-(--tgui--hint_color)">
          Нет постера
        </div>
      )}
    </div>
  )

  if (href == null) {
    return (
      <div
        className="block overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)"
        aria-label={`«${title}» в списке «Позже»`}
      >
        {inner}
      </div>
    )
  }

  return (
    <Link
      to={href}
      className="block overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) no-underline"
      aria-label={`Открыть «${title}»`}
    >
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
