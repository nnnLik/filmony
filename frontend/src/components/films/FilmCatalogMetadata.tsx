import { Play } from 'lucide-react'

import {
  formatFilmAgeLimit,
  formatFilmDurationMinutes,
  formatFilmRating,
  formatFilmSlogan,
  hasFilmPassportData,
  joinFilmWatchProviders,
} from '../../lib/filmPassportDisplay'
import { ratingPalette } from '../../lib/ratingDisplay'

export type FilmMetadataFields = {
  film_length?: number | null
  slogan?: string | null
  rating_age_limits?: string | null
  rating_kinopoisk?: number | null
  rating_imdb?: number | null
  trailer_youtube_url?: string | null
  watch_providers_ru?: string[] | null
  tmdb_recommendations?: string[] | null
}

type Size = 'sm' | 'md'

const NEUTRAL_CHIP: Record<Size, string> = {
  sm: 'rounded-md border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-1.5 py-0.5 text-[10px] font-medium leading-tight text-(--tgui--hint_color)',
  md: 'rounded-lg border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-0.5 text-[11px] font-medium leading-tight text-(--tgui--hint_color)',
}

const ACTION_CHIP: Record<Size, string> = {
  sm: 'inline-flex shrink-0 items-center gap-1 rounded-md border border-[color-mix(in_srgb,var(--tgui--link_color)_35%,transparent)] bg-[color-mix(in_srgb,var(--tgui--link_color)_10%,var(--tgui--secondary_bg_color))] px-1.5 py-0.5 text-[10px] font-semibold leading-tight text-(--tgui--link_color) no-underline transition active:opacity-80',
  md: 'inline-flex shrink-0 items-center gap-1 rounded-lg border border-[color-mix(in_srgb,var(--tgui--link_color)_35%,transparent)] bg-[color-mix(in_srgb,var(--tgui--link_color)_10%,var(--tgui--secondary_bg_color))] px-2 py-0.5 text-[11px] font-semibold leading-tight text-(--tgui--link_color) no-underline transition active:opacity-80',
}

const SIMILAR_PILL: Record<Size, string> = {
  sm: 'max-w-[9.5rem] shrink-0 truncate rounded-md border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-1 text-[10px] font-medium text-(--tgui--text_color)',
  md: 'max-w-[10.5rem] shrink-0 truncate rounded-lg border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2.5 py-1 text-[11px] font-medium text-(--tgui--text_color)',
}

function ratingChipClass(size: Size): string {
  return size === 'md'
    ? 'inline-flex items-center gap-1 rounded-lg border px-2 py-0.5 text-[11px] font-semibold leading-tight'
    : 'inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-semibold leading-tight'
}

function RatingChip({
  label,
  value,
  size,
}: {
  label: string
  value: number
  size: Size
}) {
  const palette = ratingPalette(value)
  const formatted = formatFilmRating(value)
  if (formatted == null) {
    return null
  }

  return (
    <span
      className={ratingChipClass(size)}
      style={{
        color: palette.text,
        borderColor: palette.ring,
        backgroundColor: palette.track,
      }}
      title={`${label} ${formatted}`}
    >
      <span className="text-[0.85em] font-bold opacity-80">{label}</span>
      <span>{formatted}</span>
    </span>
  )
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
      «{normalized}»
    </p>
  )
}

export function FilmMetadataChips({
  filmLength,
  ratingAgeLimits,
  ratingKinopoisk,
  ratingImdb,
  size = 'md',
  className = '',
}: {
  filmLength?: number | null
  ratingAgeLimits?: string | null
  ratingKinopoisk?: number | null
  ratingImdb?: number | null
  size?: Size
  className?: string
}) {
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
  const chip = NEUTRAL_CHIP[size]

  return (
    <div className={`flex max-w-full flex-wrap items-center gap-1 ${className}`.trim()}>
      {duration != null ? <span className={chip}>{duration}</span> : null}
      {ageLimit != null ? <span className={chip}>{ageLimit}</span> : null}
      {ratingKinopoisk != null && ratingKinopoisk > 0 ? (
        <RatingChip label="КП" value={ratingKinopoisk} size={size} />
      ) : null}
      {ratingImdb != null && ratingImdb > 0 ? (
        <RatingChip label="IMDb" value={ratingImdb} size={size} />
      ) : null}
    </div>
  )
}

export function FilmTrailerChip({
  trailerYoutubeUrl,
  size = 'md',
  className = '',
}: {
  trailerYoutubeUrl?: string | null
  size?: Size
  className?: string
}) {
  const url = trailerYoutubeUrl?.trim() ?? ''
  if (url === '') {
    return null
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={`${ACTION_CHIP[size]} ${className}`.trim()}
      aria-label="Открыть трейлер на YouTube"
    >
      <Play className="size-3 shrink-0" aria-hidden strokeWidth={2.25} />
      Трейлер
    </a>
  )
}

export function FilmWatchProvidersChips({
  providers,
  size = 'md',
  className = '',
}: {
  providers?: string[] | null
  size?: Size
  className?: string
}) {
  const names = (providers ?? []).map((name) => name.trim()).filter((name) => name !== '')
  if (names.length === 0) {
    return null
  }

  const chip = NEUTRAL_CHIP[size]
  const visible = names.slice(0, 4)
  const remainder = names.length - visible.length

  return (
    <div className={className}>
      <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-(--tgui--hint_color) sm:text-[11px]">
        Где смотреть
      </p>
      <div className="flex max-w-full flex-wrap items-center gap-1">
        {visible.map((name) => (
          <span key={name} className={chip} title={name}>
            {name}
          </span>
        ))}
        {remainder > 0 ? (
          <span className="text-[10px] font-semibold text-(--tgui--hint_color)">+{remainder}</span>
        ) : null}
      </div>
    </div>
  )
}

export function FilmSimilarTitlesScroll({
  titles,
  size = 'md',
  className = '',
}: {
  titles?: string[] | null
  size?: Size
  className?: string
}) {
  const normalized = (titles ?? []).map((title) => title.trim()).filter((title) => title !== '')
  if (normalized.length === 0) {
    return null
  }

  return (
    <div className={className}>
      <p className="mb-1.5 px-0.5 text-[10px] font-semibold uppercase tracking-wide text-(--tgui--hint_color) sm:text-[11px]">
        Похожие
      </p>
      <div className="flex gap-1.5 overflow-x-auto pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {normalized.map((title) => (
          <span key={title} className={SIMILAR_PILL[size]} title={title}>
            {title}
          </span>
        ))}
      </div>
    </div>
  )
}

export type FilmCatalogMetadataProps = {
  film: FilmMetadataFields
  size?: Size
  showSimilar?: boolean
  showProviders?: boolean
  className?: string
}

export function FilmCatalogMetadata({
  film,
  size = 'md',
  showSimilar = true,
  showProviders = true,
  className = '',
}: FilmCatalogMetadataProps) {
  const hasPassport = hasFilmPassportData(film)
  const hasTrailer = (film.trailer_youtube_url?.trim() ?? '') !== ''
  const hasSimilar = showSimilar && (film.tmdb_recommendations?.length ?? 0) > 0
  const hasProviders =
    showProviders && joinFilmWatchProviders(film.watch_providers_ru) != null

  if (!formatFilmSlogan(film.slogan) && !hasPassport && !hasTrailer && !hasSimilar && !hasProviders) {
    return null
  }

  return (
    <div className={`space-y-2 ${className}`.trim()}>
      <FilmSlogan slogan={film.slogan} />
      {hasPassport || hasTrailer ? (
        <div className="flex max-w-full flex-wrap items-center gap-1.5">
          <FilmMetadataChips
            filmLength={film.film_length}
            ratingAgeLimits={film.rating_age_limits}
            ratingKinopoisk={film.rating_kinopoisk}
            ratingImdb={film.rating_imdb}
            size={size}
          />
          <FilmTrailerChip trailerYoutubeUrl={film.trailer_youtube_url} size={size} />
        </div>
      ) : null}
      {hasProviders ? (
        <FilmWatchProvidersChips providers={film.watch_providers_ru} size={size} />
      ) : null}
      {hasSimilar ? (
        <FilmSimilarTitlesScroll titles={film.tmdb_recommendations} size={size} />
      ) : null}
    </div>
  )
}

/** @deprecated Use FilmMetadataChips */
export const FilmPassportRow = FilmMetadataChips
/** @deprecated Use FilmTrailerChip */
export const FilmTrailerLink = FilmTrailerChip
/** @deprecated Use FilmWatchProvidersChips */
export const FilmWatchProvidersRow = FilmWatchProvidersChips
/** @deprecated Use FilmSimilarTitlesScroll */
export const FilmSimilarTitles = FilmSimilarTitlesScroll
