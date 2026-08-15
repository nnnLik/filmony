import { formatFilmSlogan, hasFilmPassportData } from '../../lib/filmPassportDisplay'
import {
  normalizeMetadataStrings,
  providersSummary,
  similarSummary,
  type FilmCatalogMetadataSize,
  type FilmCatalogMetadataVariant,
} from '../../lib/filmCatalogMetadataDisplay'
import { CollapsibleFilmMetaSection } from './CollapsibleFilmMetaSection'
import { FilmPassportInline } from './FilmPassportInline'

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

const PROVIDER_CHIP: Record<FilmCatalogMetadataSize, string> = {
  sm: 'rounded-md border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-1.5 py-0.5 text-[10px] font-medium leading-tight text-(--tgui--text_color)',
  md: 'rounded-lg border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-0.5 text-[11px] font-medium leading-tight text-(--tgui--text_color)',
}

const SIMILAR_PILL: Record<FilmCatalogMetadataSize, string> = {
  sm: 'max-w-[9.5rem] shrink-0 truncate rounded-md border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-1 text-[10px] font-medium text-(--tgui--text_color)',
  md: 'max-w-[10.5rem] shrink-0 truncate rounded-lg border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2.5 py-1 text-[11px] font-medium text-(--tgui--text_color)',
}

function FilmSlogan({ slogan, className = '' }: { slogan?: string | null; className?: string }) {
  const normalized = formatFilmSlogan(slogan)
  if (normalized == null) {
    return null
  }

  return (
    <p className={`line-clamp-2 text-xs italic text-(--tgui--hint_color) sm:text-sm ${className}`.trim()}>
      «{normalized}»
    </p>
  )
}

function FilmWatchProvidersList({
  providers,
  size = 'md',
}: {
  providers: string[]
  size?: FilmCatalogMetadataSize
}) {
  if (providers.length === 0) {
    return null
  }

  const chip = PROVIDER_CHIP[size]

  return (
    <div className="flex max-w-full flex-wrap items-center gap-1">
      {providers.map((name) => (
        <span key={name} className={chip} title={name}>
          {name}
        </span>
      ))}
    </div>
  )
}

function FilmSimilarTitlesScroll({
  titles,
  size = 'md',
}: {
  titles: string[]
  size?: FilmCatalogMetadataSize
}) {
  if (titles.length === 0) {
    return null
  }

  return (
    <div className="flex gap-1.5 overflow-x-auto pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {titles.map((title) => (
        <span key={title} className={SIMILAR_PILL[size]} title={title}>
          {title}
        </span>
      ))}
    </div>
  )
}

export type FilmCatalogMetadataProps = {
  film: FilmMetadataFields
  size?: FilmCatalogMetadataSize
  variant?: FilmCatalogMetadataVariant
  showSimilar?: boolean
  showProviders?: boolean
  showSlogan?: boolean
  className?: string
}

export function FilmCatalogMetadata({
  film,
  size = 'md',
  variant = 'full',
  showSimilar = true,
  showProviders = true,
  showSlogan = true,
  className = '',
}: FilmCatalogMetadataProps) {
  const isCompact = variant === 'compact'
  const hasPassport = hasFilmPassportData(film)
  const hasTrailer = (film.trailer_youtube_url?.trim() ?? '') !== ''
  const providerNames = normalizeMetadataStrings(film.watch_providers_ru)
  const similarTitles = normalizeMetadataStrings(film.tmdb_recommendations)
  const hasSimilar = !isCompact && showSimilar && similarTitles.length > 0
  const hasProviders = !isCompact && showProviders && providerNames.length > 0
  const showSloganBlock = !isCompact && showSlogan && formatFilmSlogan(film.slogan) != null

  if (!showSloganBlock && !hasPassport && !hasTrailer && !hasSimilar && !hasProviders) {
    return null
  }

  return (
    <div className={`space-y-1.5 ${className}`.trim()}>
      {showSloganBlock ? <FilmSlogan slogan={film.slogan} /> : null}
      {hasPassport || hasTrailer ? (
        <FilmPassportInline
          filmLength={film.film_length}
          ratingAgeLimits={film.rating_age_limits}
          ratingKinopoisk={film.rating_kinopoisk}
          ratingImdb={film.rating_imdb}
          trailerYoutubeUrl={film.trailer_youtube_url}
          size={size}
          variant={variant}
        />
      ) : null}
      {hasProviders ? (
        <CollapsibleFilmMetaSection
          title="Где смотреть"
          summary={providersSummary(providerNames)}
          size={size}
        >
          <FilmWatchProvidersList providers={providerNames} size={size} />
        </CollapsibleFilmMetaSection>
      ) : null}
      {hasSimilar ? (
        <CollapsibleFilmMetaSection title="Похожие" summary={similarSummary(similarTitles)} size={size}>
          <FilmSimilarTitlesScroll titles={similarTitles} size={size} />
        </CollapsibleFilmMetaSection>
      ) : null}
    </div>
  )
}
