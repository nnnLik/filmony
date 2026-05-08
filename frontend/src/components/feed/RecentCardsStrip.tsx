import { Link } from 'react-router-dom'

import type { RecentCardViewSnapshot } from '../../lib/recentCardViews'

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
    <section className="border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_55%,transparent)] px-4 py-2.5">
      <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-(--tgui--hint_color)">Недавно открывали</p>
      <div className="flex gap-3 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {items.map((row) => (
          <Link
            key={row.id}
            to={`/cards/${row.id}`}
            className="flex w-18 shrink-0 flex-col gap-1 no-underline"
          >
            <div className="aspect-2/3 w-full overflow-hidden rounded-lg border border-(--tgui--divider_color) bg-(--tgui--bg_color)">
              {row.film_poster_url ? (
                <img src={row.film_poster_url} alt="" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center px-1 text-center text-[10px] text-(--tgui--hint_color)">
                  Нет постера
                </div>
              )}
            </div>
            <span className="line-clamp-2 text-center text-[11px] leading-tight text-(--tgui--text_color)">
              {titleShort(row.film_title, 28)}
            </span>
          </Link>
        ))}
      </div>
    </section>
  )
}
