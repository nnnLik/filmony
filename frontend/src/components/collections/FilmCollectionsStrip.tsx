import { Link } from 'react-router'

import type { CollectionSummary } from '../../api/collectionsTypes'
import { collectionProgressPercent } from '../../lib/collectionProgress'

export type FilmCollectionsStripProps = {
  items: CollectionSummary[] | null
  className?: string
}

function FilmCollectionsSkeleton() {
  return (
    <div
      className="mt-3 flex gap-2 overflow-hidden"
      aria-hidden
    >
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="h-9 w-36 shrink-0 animate-pulse rounded-full bg-[color-mix(in_srgb,var(--tgui--hint_color)_14%,transparent)]"
        />
      ))}
    </div>
  )
}

export function FilmCollectionsStrip({ items, className = '' }: FilmCollectionsStripProps) {
  if (items != null && items.length === 0) {
    return null
  }

  return (
    <section
      className={`rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:p-4 ${className}`.trim()}
    >
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">
        В коллекциях
      </p>
      {items == null ? (
        <FilmCollectionsSkeleton />
      ) : (
        <ul className="mt-3 -mx-1 flex list-none gap-2 overflow-x-auto px-1 pb-0.5 scrollbar-none">
          {items.map((collection) => {
            const percent =
              collection.viewer_progress != null
                ? collectionProgressPercent(collection.viewer_progress)
                : null
            return (
              <li key={collection.slug} className="shrink-0">
                <Link
                  to={`/collections/${encodeURIComponent(collection.slug)}`}
                  className="inline-flex max-w-[16rem] items-center gap-2 rounded-full border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] px-3 py-2 no-underline outline-none transition-[background-color] active:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)] focus-visible:ring-2 focus-visible:ring-(--tgui--link_color)"
                >
                  <span className="truncate text-sm font-semibold text-(--tgui--text_color)">
                    {collection.title}
                  </span>
                  {percent != null ? (
                    <span className="shrink-0 text-xs font-semibold tabular-nums text-(--filmony-mint,#5eead4)">
                      {percent}%
                    </span>
                  ) : null}
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
