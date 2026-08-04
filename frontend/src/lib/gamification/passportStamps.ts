export type PassportStampCategory =
  | 'country'
  | 'decade'
  | 'yearly'
  | 'milestone'
  | 'meta'
  | 'director'
  | 'genre'
  | 'vibe'
  | 'extreme'

export type PassportStampMeta = {
  title: string
  description: string
  category: PassportStampCategory
}

export type StampDisplayFields = {
  stamp_id: string
  title?: string | null
  description?: string | null
  unlock_film_poster_url?: string | null
  unlock_poster_url?: string | null
}

export const DYNAMIC_LIST_STAMP_CATEGORIES: readonly PassportStampCategory[] = ['director', 'country'] as const

export const COLLAPSED_STAMP_LIST_LIMIT = 8

export function isDynamicListStampCategory(category: PassportStampCategory): boolean {
  return category === 'director' || category === 'country'
}

export function getStampPosterUrl(stamp: StampDisplayFields): string | null {
  return stamp.unlock_film_poster_url ?? stamp.unlock_poster_url ?? null
}

export function getStampDisplayTitle(stamp: StampDisplayFields): string {
  const apiTitle = stamp.title?.trim()
  if (apiTitle != null && apiTitle !== '') {
    return apiTitle
  }
  return getPassportStampMeta(stamp.stamp_id).title
}

export function getStampDisplayDescription(stamp: StampDisplayFields): string {
  const apiDescription = stamp.description?.trim()
  if (apiDescription != null && apiDescription !== '') {
    return apiDescription
  }
  return getPassportStampMeta(stamp.stamp_id).description
}

export function parseDirectorFirstKinopoiskId(stampId: string): string | null {
  const match = /^director_first_(\d+)$/.exec(stampId)
  return match?.[1] ?? null
}

const DECADE_LABELS: Record<number, string> = {
  1960: '1960‑е',
  1970: '1970‑е',
  1980: '1980‑е',
  1990: '1990‑е',
  2000: '2000‑е',
  2010: '2010‑е',
  2020: '2020‑е',
}

const COUNTRY_TOTAL_TARGETS: Record<number, string> = {
  5: '5 стран',
  10: '10 стран',
  20: '20 стран',
}

const GENRE_TOTAL_TARGETS: Record<number, string> = {
  5: '5 жанров',
  10: '10 жанров',
  15: '15 жанров',
}

const DIRECTOR_FAN_TARGETS: Record<number, string> = {
  3: '3 фильма режиссёра',
  5: '5 фильмов режиссёра',
  10: '10 фильмов режиссёра',
}

function slugToTitle(slug: string): string {
  return slug
    .split(/[-_]+/)
    .filter((part) => part !== '')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function getPassportStampMeta(stampId: string): PassportStampMeta {
  if (stampId === 'first_rating_10') {
    return {
      title: 'Первая десятка',
      description: 'Первый фильм, которому вы поставили 10.',
      category: 'extreme',
    }
  }

  if (stampId === 'first_rating_1') {
    return {
      title: 'Первая единица',
      description: 'Первый фильм, которому вы поставили 1.',
      category: 'extreme',
    }
  }

  if (stampId === 'binge_day') {
    return {
      title: 'Кинобinge',
      description: 'Несколько оценок за один календарный день.',
      category: 'vibe',
    }
  }

  if (stampId === 'horror_survivor') {
    return {
      title: 'Horror survivor',
      description: 'Выжили после хоррора и всё равно поставили оценку.',
      category: 'genre',
    }
  }

  if (stampId === 'high_streak_3') {
    return {
      title: 'Горячая серия',
      description: 'Три высокие оценки подряд (9+).',
      category: 'vibe',
    }
  }

  if (stampId === 'mood_swings') {
    return {
      title: 'Качели настроения',
      description: 'Резкий контраст настроений «до» и «после» просмотра.',
      category: 'vibe',
    }
  }

  if (stampId === 'year_first_rated') {
    return {
      title: 'Первый тайтл года',
      description: 'Первая оценка в календарном году.',
      category: 'meta',
    }
  }

  if (stampId.startsWith('year_first_rated_')) {
    const year = stampId.slice('year_first_rated_'.length)
    return {
      title: `Первый просмотр ${year}`,
      description: `Первая оценка в ${year} году.`,
      category: 'yearly',
    }
  }

  if (stampId.startsWith('chrono_year_')) {
    const year = stampId.slice('chrono_year_'.length)
    return {
      title: `Хронология ${year}`,
      description: `Оценки фильмов, вышедших в ${year} году.`,
      category: 'yearly',
    }
  }

  if (stampId.startsWith('country_first_')) {
    const slug = stampId.slice('country_first_'.length)
    return {
      title: `Первый из ${slugToTitle(slug)}`,
      description: 'Первая оценка фильма из этой страны.',
      category: 'country',
    }
  }

  if (stampId.startsWith('decade_first_')) {
    const decade = Number(stampId.slice('decade_first_'.length))
    const label = DECADE_LABELS[decade] ?? `${decade}-е`
    return {
      title: `Первый из ${label}`,
      description: 'Первая оценка фильма этого десятилетия.',
      category: 'decade',
    }
  }

  if (stampId.startsWith('director_first_')) {
    const slug = stampId.slice('director_first_'.length)
    return {
      title: `Первый раз: ${slugToTitle(slug)}`,
      description: 'Первая оценка фильма этого режиссёра.',
      category: 'director',
    }
  }

  if (stampId.startsWith('director_fan_')) {
    const targetRaw = stampId.slice('director_fan_'.length)
    const target = Number(targetRaw)
    const label = DIRECTOR_FAN_TARGETS[target] ?? `${targetRaw} фильмов режиссёра`
    return {
      title: label,
      description: 'Оценённые фильмы одного режиссёра.',
      category: 'director',
    }
  }

  if (stampId.startsWith('genres_total_')) {
    const target = Number(stampId.slice('genres_total_'.length))
    const label = GENRE_TOTAL_TARGETS[target] ?? `${target} жанров`
    return {
      title: label,
      description: 'Уникальные жанры среди всех оценённых фильмов.',
      category: 'genre',
    }
  }

  if (stampId.startsWith('countries_5_in_')) {
    const year = stampId.slice('countries_5_in_'.length)
    return {
      title: `5 стран в ${year}`,
      description: 'Пять разных стран среди оценок за календарный год.',
      category: 'yearly',
    }
  }

  if (stampId.startsWith('countries_total_')) {
    const target = Number(stampId.slice('countries_total_'.length))
    const label = COUNTRY_TOTAL_TARGETS[target] ?? `${target} стран`
    return {
      title: label,
      description: 'Уникальные страны среди всех оценённых фильмов.',
      category: 'milestone',
    }
  }

  return {
    title: stampId,
    description: 'Коллекционный штамп кино-паспорта.',
    category: 'meta',
  }
}

export const PASSPORT_STAMP_CATEGORY_ORDER: readonly PassportStampCategory[] = [
  'director',
  'country',
  'decade',
  'genre',
  'yearly',
  'vibe',
  'extreme',
  'milestone',
  'meta',
] as const

export const PASSPORT_STAMP_CATEGORY_LABELS: Record<PassportStampCategory, string> = {
  director: 'Режиссёры',
  country: 'Страны',
  decade: 'Десятилетия',
  genre: 'Жанры',
  yearly: 'Годы',
  vibe: 'Настроение',
  extreme: 'Экстрим',
  milestone: 'Вехи',
  meta: 'Прочее',
}

/** Known stamp ids for stable grid ordering when API returns sparse lists. */
export const PASSPORT_STAMP_CATALOG_IDS: readonly string[] = [
  'year_first_rated',
  'first_rating_10',
  'first_rating_1',
  'binge_day',
  'horror_survivor',
  'high_streak_3',
  'mood_swings',
  ...Object.keys(DECADE_LABELS).map((decade) => `decade_first_${decade}`),
  'countries_total_5',
  'countries_total_10',
  'countries_total_20',
  'genres_total_5',
  'genres_total_10',
  'genres_total_15',
  'director_fan_3',
  'director_fan_5',
  'director_fan_10',
] as const
