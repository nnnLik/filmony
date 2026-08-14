export function formatFilmDurationMinutes(minutes: number | null | undefined): string | null {
  if (minutes == null || !Number.isFinite(minutes) || minutes <= 0) {
    return null
  }
  const total = Math.round(minutes)
  const hours = Math.floor(total / 60)
  const rest = total % 60
  if (hours > 0 && rest > 0) {
    return `${hours}ч ${rest}м`
  }
  if (hours > 0) {
    return `${hours}ч`
  }
  return `${total} мин`
}

export function formatFilmAgeLimit(raw: string | null | undefined): string | null {
  if (raw == null) return null
  const trimmed = raw.trim()
  if (trimmed === '') return null
  const match = /^age(\d+)$/i.exec(trimmed)
  if (match != null) {
    return `${match[1]}+`
  }
  return trimmed
}

export function formatFilmRating(value: number | null | undefined): string | null {
  if (value == null || !Number.isFinite(value) || value <= 0) {
    return null
  }
  return value.toFixed(1)
}

export function hasFilmPassportData(film: {
  film_length?: number | null
  rating_age_limits?: string | null
  rating_kinopoisk?: number | null
  rating_imdb?: number | null
}): boolean {
  return (
    formatFilmDurationMinutes(film.film_length) != null ||
    formatFilmAgeLimit(film.rating_age_limits) != null ||
    formatFilmRating(film.rating_kinopoisk) != null ||
    formatFilmRating(film.rating_imdb) != null
  )
}

export function formatFilmSlogan(slogan: string | null | undefined): string | null {
  if (slogan == null) return null
  const trimmed = slogan.trim()
  return trimmed === '' ? null : trimmed
}

export function joinFilmWatchProviders(names: string[] | null | undefined): string | null {
  const normalized = (names ?? []).map((name) => name.trim()).filter((name) => name !== '')
  if (normalized.length === 0) {
    return null
  }
  return normalized.join(' · ')
}
