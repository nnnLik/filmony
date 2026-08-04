import { Link } from 'react-router'

import type { RecentCardViewSnapshot } from '../../lib/recentCardViews'
import { PosterStrip } from '../cards/PosterStrip'
import { PosterTile } from '../cards/PosterTile'

function titleShort(title: string, max = 32): string {
  const t = title.replace(/\s+/g, ' ').trim()
  if (t.length <= max) return t
  return `${t.slice(0, max - 1)}…`
}

export type RecentCardsStripProps = {
  items: RecentCardViewSnapshot[]
}

export function RecentCardsStrip({ items }: RecentCardsStripProps) {
  if (items.length === 0) return null
  return (
    <PosterStrip title="Недавно открывали">
      {items.map((row) => (
        <Link
          key={row.id}
          to={`/cards/${row.id}`}
          className="flex w-18 shrink-0 flex-col gap-1 no-underline"
        >
          <PosterTile
            posterUrl={row.film_poster_url}
            title={row.film_title}
            rounded="lg"
            shellClassName="bg-(--tgui--bg_color)"
          />
          <span className="line-clamp-2 text-center text-[11px] leading-tight text-(--tgui--text_color)">
            {titleShort(row.film_title, 28)}
          </span>
        </Link>
      ))}
    </PosterStrip>
  )
}
