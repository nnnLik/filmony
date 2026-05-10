import type { GetUserCardsParams, ProfileCardsSort } from '../api/profileApi'
import type { CardCompany, CardMoodAfter, CardMoodBefore } from '../api/profileTypes'

export type RatedCardsListQuery = {
  sort: ProfileCardsSort
  /** Кастомные теги владельца профиля; на бэкенде пересечение (AND). */
  tags: string[]
  yearMin: string
  yearMax: string
  company: CardCompany | ''
  moodBefore: CardMoodBefore | ''
  moodAfter: CardMoodAfter | ''
}

export const DEFAULT_RATED_CARDS_QUERY: RatedCardsListQuery = {
  sort: 'recent',
  tags: [],
  yearMin: '',
  yearMax: '',
  company: '',
  moodBefore: '',
  moodAfter: '',
}

export function isDefaultRatedCardsQuery(q: RatedCardsListQuery): boolean {
  return (
    q.sort === 'recent' &&
    q.tags.length === 0 &&
    q.yearMin.trim() === '' &&
    q.yearMax.trim() === '' &&
    q.company === '' &&
    q.moodBefore === '' &&
    q.moodAfter === ''
  )
}

export function ratedCardsQueryKey(q: RatedCardsListQuery): string {
  return JSON.stringify({
    sort: q.sort,
    tags: [...q.tags].sort(),
    ym: q.yearMin.trim(),
    yx: q.yearMax.trim(),
    co: q.company,
    mb: q.moodBefore,
    ma: q.moodAfter,
  })
}

/** Базовые query-параметры для GET /users/.../cards (без cursor / limit / favorites). */
export function ratedCardsToListParams(q: RatedCardsListQuery): Omit<
  GetUserCardsParams,
  'cursor' | 'limit' | 'favoritesOnly'
> {
  const ymn = q.yearMin.trim()
  const ymx = q.yearMax.trim()
  const yearMin = ymn === '' ? null : Number(ymn)
  const yearMax = ymx === '' ? null : Number(ymx)

  return {
    sort: q.sort,
    tags: q.tags.length > 0 ? q.tags : undefined,
    yearMin: yearMin != null && Number.isFinite(yearMin) ? yearMin : null,
    yearMax: yearMax != null && Number.isFinite(yearMax) ? yearMax : null,
    company: q.company === '' ? null : q.company,
    moodBefore: q.moodBefore === '' ? null : q.moodBefore,
    moodAfter: q.moodAfter === '' ? null : q.moodAfter,
  }
}
