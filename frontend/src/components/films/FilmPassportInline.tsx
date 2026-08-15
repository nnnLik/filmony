import { IconButton } from '@telegram-apps/telegram-ui'
import { Play } from 'lucide-react'
import type { ReactNode } from 'react'

import {
  formatFilmAgeLimit,
  formatFilmDurationMinutes,
  formatFilmRating,
} from '../../lib/filmPassportDisplay'
import {
  FILM_CATALOG_TEXT_SIZE,
  type FilmCatalogMetadataSize,
  type FilmCatalogMetadataVariant,
} from '../../lib/filmCatalogMetadataDisplay'
import { openExternalUrl } from '../../lib/openExternalUrl'
import { ratingPalette } from '../../lib/ratingDisplay'

function InlineRating({ label, value }: { label: string; value: number }) {
  const palette = ratingPalette(value)
  const formatted = formatFilmRating(value)
  if (formatted == null) {
    return null
  }

  return (
    <span className="font-semibold tabular-nums" style={{ color: palette.text }} title={`${label} ${formatted}`}>
      {label} {formatted}
    </span>
  )
}

function MetaSeparator() {
  return <span className="text-(--tgui--hint_color) opacity-60">·</span>
}

const TRAILER_LINK: Record<FilmCatalogMetadataSize, string> = {
  sm: 'inline-flex shrink-0 items-center gap-0.5 rounded-md border border-[color-mix(in_srgb,var(--tgui--link_color)_35%,transparent)] bg-[color-mix(in_srgb,var(--tgui--link_color)_10%,var(--tgui--secondary_bg_color))] px-1.5 py-0.5 font-semibold text-(--tgui--link_color) no-underline transition active:opacity-80',
  md: 'inline-flex shrink-0 items-center gap-1 rounded-lg border border-[color-mix(in_srgb,var(--tgui--link_color)_35%,transparent)] bg-[color-mix(in_srgb,var(--tgui--link_color)_10%,var(--tgui--secondary_bg_color))] px-2 py-0.5 font-semibold text-(--tgui--link_color) no-underline transition active:opacity-80',
}

export type FilmPassportInlineProps = {
  filmLength?: number | null
  ratingAgeLimits?: string | null
  ratingKinopoisk?: number | null
  ratingImdb?: number | null
  trailerYoutubeUrl?: string | null
  showTrailerPlaceholder?: boolean
  size?: FilmCatalogMetadataSize
  variant?: FilmCatalogMetadataVariant
  className?: string
}

export function FilmTrailerIconButton({
  trailerYoutubeUrl,
  className = '',
}: {
  trailerYoutubeUrl?: string | null
  className?: string
}) {
  const url = trailerYoutubeUrl?.trim() ?? ''
  if (url === '') {
    return null
  }

  return (
    <IconButton
      type="button"
      size="s"
      mode="gray"
      className={className}
      aria-label="Открыть трейлер на YouTube"
      onClick={() => openExternalUrl(url)}
    >
      <Play className="relative z-1 block size-[18px]" strokeWidth={1.75} aria-hidden />
    </IconButton>
  )
}

export function FilmPassportInline({
  filmLength,
  ratingAgeLimits,
  ratingKinopoisk,
  ratingImdb,
  trailerYoutubeUrl,
  showTrailerPlaceholder = true,
  size = 'md',
  variant: _variant = 'full',
  className = '',
}: FilmPassportInlineProps) {
  const duration = formatFilmDurationMinutes(filmLength)
  const ageLimit = formatFilmAgeLimit(ratingAgeLimits)
  const trailerUrl = trailerYoutubeUrl?.trim() ?? ''
  const hasRatings =
    (ratingKinopoisk != null && ratingKinopoisk > 0) || (ratingImdb != null && ratingImdb > 0)
  const hasNeutral = duration != null || ageLimit != null

  if (!hasNeutral && !hasRatings && trailerUrl === '') {
    return null
  }

  const items: ReactNode[] = []

  if (duration != null) {
    items.push(
      <span key="duration" className="text-(--tgui--hint_color)">
        {duration}
      </span>,
    )
  }
  if (ageLimit != null) {
    items.push(
      <span key="age" className="text-(--tgui--hint_color)">
        {ageLimit}
      </span>,
    )
  }
  if (ratingKinopoisk != null && ratingKinopoisk > 0) {
    items.push(<InlineRating key="kp" label="КП" value={ratingKinopoisk} />)
  }
  if (ratingImdb != null && ratingImdb > 0) {
    items.push(<InlineRating key="imdb" label="IMDb" value={ratingImdb} />)
  }

  return (
    <p className={`flex max-w-full flex-wrap items-center gap-x-1.5 gap-y-1 ${FILM_CATALOG_TEXT_SIZE[size]} ${className}`.trim()}>
      {items.map((item, index) => (
        <span key={index} className="inline-flex items-center gap-x-1.5">
          {index > 0 ? <MetaSeparator /> : null}
          {item}
        </span>
      ))}
      {trailerUrl !== '' ? (
        <span className="inline-flex items-center gap-x-1.5">
          {items.length > 0 ? <MetaSeparator /> : null}
          <a
            href={trailerUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={TRAILER_LINK[size]}
            aria-label="Открыть трейлер на YouTube"
            onClick={(event) => {
              event.preventDefault()
              openExternalUrl(trailerUrl)
            }}
          >
            <Play className="size-3 shrink-0" aria-hidden strokeWidth={2.25} />
            <span>Трейлер</span>
          </a>
        </span>
      ) : showTrailerPlaceholder && (hasNeutral || hasRatings) ? (
        <span className="inline-flex items-center gap-x-1.5">
          {items.length > 0 ? <MetaSeparator /> : null}
          <span className="text-(--tgui--hint_color)">Трейлер пока недоступен</span>
        </span>
      ) : null}
    </p>
  )
}
