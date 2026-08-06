import { Link } from 'react-router'

import type { CollectionSummary, UserCollectionProgress } from '../../api/collectionsTypes'
import { CollectionProgressBar } from './CollectionProgressBar'

function descriptionSnippet(description: string | null, maxLen = 120): string | null {
  if (description == null || description.trim() === '') {
    return null
  }
  const trimmed = description.trim()
  if (trimmed.length <= maxLen) {
    return trimmed
  }
  return `${trimmed.slice(0, maxLen - 1).trimEnd()}…`
}

function progressPercent(progress: UserCollectionProgress): number {
  if (progress.total_count <= 0) {
    return 0
  }
  return Math.min(100, Math.round((progress.rated_count / progress.total_count) * 100))
}

type CollectionListItemProps = {
  collection: CollectionSummary
}

export function CollectionListItem({ collection }: CollectionListItemProps) {
  const snippet = descriptionSnippet(collection.description)
  const percent =
    collection.viewer_progress != null ? progressPercent(collection.viewer_progress) : null

  return (
    <li>
      <Link
        to={`/collections/${encodeURIComponent(collection.slug)}`}
        className="block rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] px-4 py-3.5 no-underline outline-none transition-[background-color,border-color] active:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)] focus-visible:ring-2 focus-visible:ring-(--tgui--link_color)"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="line-clamp-2 text-[15px] font-semibold text-(--tgui--text_color)">
              {collection.title}
            </p>
            {snippet != null ? (
              <p className="mt-1 line-clamp-2 text-sm text-(--tgui--hint_color)">{snippet}</p>
            ) : null}
            <p className="mt-1.5 text-xs text-(--tgui--hint_color)">
              {collection.film_count}{' '}
              {collection.film_count === 1
                ? 'фильм'
                : collection.film_count >= 2 && collection.film_count <= 4
                  ? 'фильма'
                  : 'фильмов'}
            </p>
          </div>
          {percent != null ? (
            <span className="shrink-0 rounded-full bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_16%,transparent)] px-2 py-0.5 text-xs font-semibold tabular-nums text-(--filmony-mint,#5eead4)">
              {percent}%
            </span>
          ) : null}
        </div>
        {collection.viewer_progress != null ? (
          <CollectionProgressBar progress={collection.viewer_progress} className="mt-3" />
        ) : null}
      </Link>
    </li>
  )
}
