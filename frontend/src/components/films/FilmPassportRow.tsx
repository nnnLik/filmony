import {
  formatFilmAgeLimit,
  formatFilmDurationMinutes,
  formatFilmRating,
  formatFilmSlogan,
  hasFilmPassportData,
  joinFilmWatchProviders,
} from '../../lib/filmPassportDisplay'

type FilmPassportRowProps = {
  filmLength?: number | null
  ratingAgeLimits?: string | null
  ratingKinopoisk?: number | null
  ratingImdb?: number | null
  className?: string
}

export function FilmSlogan({
  slogan,
  className = '',
}: {
  slogan?: string | null
  className?: string
}) {
  const normalized = formatFilmSlogan(slogan)
  if (normalized == null) {
    return null
  }

  return (
    <p className={`text-xs italic text-(--tgui--hint_color) sm:text-sm ${className}`.trim()}>
      {normalized}
    </p>
  )
}

export function FilmPassportRow({
  filmLength,
  ratingAgeLimits,
  ratingKinopoisk,
  ratingImdb,
  className = '',
}: FilmPassportRowProps) {
  if (
    !hasFilmPassportData({
      film_length: filmLength,
      rating_age_limits: ratingAgeLimits,
      rating_kinopoisk: ratingKinopoisk,
      rating_imdb: ratingImdb,
    })
  ) {
    return null
  }

  const duration = formatFilmDurationMinutes(filmLength)
  const ageLimit = formatFilmAgeLimit(ratingAgeLimits)
  const kpRating = formatFilmRating(ratingKinopoisk)
  const imdbRating = formatFilmRating(ratingImdb)

  const parts: string[] = []
  if (duration != null) parts.push(duration)
  if (ageLimit != null) parts.push(ageLimit)
  if (kpRating != null) parts.push(`КП ${kpRating}`)
  if (imdbRating != null) parts.push(`IMDb ${imdbRating}`)

  return (
    <p className={`text-xs text-(--tgui--hint_color) sm:text-sm ${className}`.trim()}>
      {parts.join(' · ')}
    </p>
  )
}

type FilmTrailerLinkProps = {
  trailerYoutubeUrl?: string | null
  className?: string
}

export function FilmTrailerLink({ trailerYoutubeUrl, className = '' }: FilmTrailerLinkProps) {
  const url = trailerYoutubeUrl?.trim() ?? ''
  if (url === '') {
    return null
  }

  return (
    <p className={className}>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs font-semibold text-(--tgui--link_color) no-underline sm:text-sm"
      >
        Трейлер
      </a>
    </p>
  )
}

type FilmWatchProvidersRowProps = {
  providers?: string[] | null
  className?: string
}

export function FilmWatchProvidersRow({ providers, className = '' }: FilmWatchProvidersRowProps) {
  const joined = joinFilmWatchProviders(providers)
  if (joined == null) {
    return null
  }

  return (
    <div className={className}>
      <p className="text-xs font-semibold text-(--tgui--text_color) sm:text-sm">Где смотреть</p>
      <p className="mt-1 text-xs text-(--tgui--hint_color) sm:text-sm">{joined}</p>
    </div>
  )
}

type FilmSimilarTitlesProps = {
  titles?: string[] | null
  className?: string
}

export function FilmSimilarTitles({ titles, className = '' }: FilmSimilarTitlesProps) {
  const normalized = (titles ?? []).map((title) => title.trim()).filter((title) => title !== '')
  if (normalized.length === 0) {
    return null
  }

  return (
    <div className={className}>
      <p className="text-xs font-semibold text-(--tgui--text_color) sm:text-sm">Похожие по TMDB</p>
      <p className="mt-1 text-xs text-(--tgui--hint_color) sm:text-sm">{normalized.join(' · ')}</p>
    </div>
  )
}
