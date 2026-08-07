import { Link } from 'react-router'

import { formatRating } from '../feed/feedCardUtils'
import { OscarReleaseYearLabel } from '../films/OscarReleaseYearLabel'
import { FilmGenreChips } from '../films/FilmGenreChips'
import { formatRatingsCount } from '../../lib/formatRuPlural'
import { primaryFilmAwardBadge, releaseYearLabel } from '../../lib/filmAwardBadgeDisplay'
import type { FilmAwardBadge } from '../../api/profileTypes'

export type CatalogRatedFilm = {
  film_id: number
  title: string
  year: number | null
  poster_url: string | null
  genres: string[]
  community_avg_rating: number | null
  ratings_count: number
  award_badges?: FilmAwardBadge[]
}

type CatalogRatedFilmRowProps = {
  film: CatalogRatedFilm
}

export function CatalogRatedFilmRow({ film }: CatalogRatedFilmRowProps) {
  const oscarBadge = primaryFilmAwardBadge(film.award_badges)

  return (
    <li>
      <Link
        to={`/films/${film.film_id}`}
        className="flex gap-3 px-3 py-3 no-underline outline-none transition-[background-color] active:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-(--tgui--link_color)"
      >
        <div className="h-[4.5rem] w-12 shrink-0 overflow-hidden rounded-lg bg-(--tgui--secondary_bg_color)">
          {film.poster_url ? (
            <img
              src={film.poster_url}
              alt=""
              className="h-full w-full object-cover"
              loading="lazy"
              decoding="async"
            />
          ) : null}
        </div>
        <div className="min-w-0 flex-1">
          <p className="line-clamp-2 text-sm font-medium text-(--tgui--text_color)">{film.title}</p>
          <div className="mt-0.5 flex flex-wrap items-center gap-1.5">
            <OscarReleaseYearLabel
              label={releaseYearLabel(film.year)}
              badge={oscarBadge}
              releaseYear={film.year}
              variant="compact"
            />
          </div>
          <FilmGenreChips genres={film.genres} maxVisible={2} className="mt-1.5" />
          <p className="mt-1 text-xs tabular-nums text-(--tgui--hint_color)">
            {film.community_avg_rating != null ? (
              <>
                <span className="font-semibold text-(--tgui--text_color)">
                  {formatRating(film.community_avg_rating)}
                </span>
                {' · '}
              </>
            ) : null}
            {formatRatingsCount(film.ratings_count)}
          </p>
        </div>
      </Link>
    </li>
  )
}
