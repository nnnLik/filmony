import { CircleCheck } from 'lucide-react'
import { Link } from 'react-router'

import type { CollectionFilmItem } from '../../api/collectionsTypes'
import { resolveApiMediaUrl } from '../../lib/resolveApiMediaUrl'

function posterSrc(url: string | null): string | undefined {
  if (url == null || url.trim() === '') {
    return undefined
  }
  const trimmed = url.trim()
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    return trimmed
  }
  return resolveApiMediaUrl(trimmed)
}

type CollectionFilmRowProps = {
  film: CollectionFilmItem
}

export function CollectionFilmRow({ film }: CollectionFilmRowProps) {
  const hasRatedState = film.viewer_has_rated != null
  const rated = film.viewer_has_rated === true
  const poster = posterSrc(film.poster_url)

  return (
    <li>
      <Link
        to={`/films/${film.film_id}`}
        className={`flex gap-3 px-3 py-3 no-underline outline-none transition-[background-color,opacity] active:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-(--tgui--link_color) ${
          hasRatedState && !rated ? 'opacity-60' : ''
        }`}
      >
        <div className="relative h-[4.5rem] w-12 shrink-0 overflow-hidden rounded-lg bg-(--tgui--secondary_bg_color)">
          {poster != null ? (
            <img
              src={poster}
              alt=""
              className="h-full w-full object-cover"
              loading="lazy"
              decoding="async"
            />
          ) : null}
          {hasRatedState && rated ? (
            <span className="absolute top-1 right-1 flex size-4 items-center justify-center rounded-full bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)]">
              <CircleCheck className="block size-4 text-emerald-500" strokeWidth={2.25} aria-hidden />
            </span>
          ) : null}
        </div>
        <div className="min-w-0 flex-1">
          <p className="line-clamp-2 text-sm font-medium text-(--tgui--text_color)">{film.title}</p>
          <p className="mt-0.5 text-xs text-(--tgui--hint_color)">{film.year ?? '—'}</p>
          {hasRatedState ? (
            <p className="mt-1 text-xs text-(--tgui--hint_color)">
              {rated ? 'Оценён' : 'Ещё не оценён'}
            </p>
          ) : null}
        </div>
      </Link>
    </li>
  )
}
