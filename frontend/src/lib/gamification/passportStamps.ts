export type PassportStampMeta = {
  title: string
  description: string
  category: 'country' | 'decade' | 'yearly' | 'milestone' | 'meta'
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

function slugToTitle(slug: string): string {
  return slug
    .split(/[-_]+/)
    .filter((part) => part !== '')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function getPassportStampMeta(stampId: string): PassportStampMeta {
  if (stampId === 'year_first_rated') {
    return {
      title: 'Первый тайтл года',
      description: 'Первая оценка в календарном году.',
      category: 'meta',
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

/** Known stamp ids for stable grid ordering when API returns sparse lists. */
export const PASSPORT_STAMP_CATALOG_IDS: readonly string[] = [
  'year_first_rated',
  ...Object.keys(DECADE_LABELS).map((decade) => `decade_first_${decade}`),
  'countries_total_5',
  'countries_total_10',
  'countries_total_20',
] as const
