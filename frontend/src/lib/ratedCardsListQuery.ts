import type { GetUserCardsParams, ProfileCardsSort } from '../api/profileApi'
import type { CardCompany, CardMoodAfter, CardMoodBefore } from '../api/profileTypes'

const PROFILE_CARDS_SORTS: ProfileCardsSort[] = ['recent', 'rating_desc', 'rating_asc']
const CARD_COMPANIES: CardCompany[] = ['alone', 'partner', 'friends', 'family']
const CARD_MOODS_BEFORE: CardMoodBefore[] = ['relax', 'laugh', 'sad', 'thrill']
const CARD_MOODS_AFTER: CardMoodAfter[] = ['laughed', 'cried', 'enjoyed', 'tense', 'wasted_time']

/** URL search-param keys owned by profile rated-cards filters. */
export const RATED_CARDS_FILTER_PARAM_KEYS = [
  'sort',
  'tags',
  'filmTitle',
  'yearMin',
  'yearMax',
  'company',
  'moodBefore',
  'moodAfter',
  'favoritesOnly',
  'categoryId',
  'completedOn',
] as const

export type RatedCardsListQuery = {
  sort: ProfileCardsSort
  tags: string[]
  filmTitle: string
  yearMin: string
  yearMax: string
  company: CardCompany | ''
  moodBefore: CardMoodBefore | ''
  moodAfter: CardMoodAfter | ''
  /** Только карточки с отметкой «в избранном» (`favorites_only` в API списков). */
  favoritesOnly: boolean
  /** Пустая строка = все полки. */
  categoryId: string
  /** ISO date YYYY-MM-DD — завершённые в этот день. */
  completedOn: string
}

export const DEFAULT_RATED_CARDS_QUERY: RatedCardsListQuery = {
  sort: 'recent',
  tags: [],
  filmTitle: '',
  yearMin: '',
  yearMax: '',
  company: '',
  moodBefore: '',
  moodAfter: '',
  favoritesOnly: false,
  categoryId: '',
  completedOn: '',
}

export function isDefaultRatedCardsQuery(q: RatedCardsListQuery): boolean {
  return (
    q.sort === 'recent' &&
    q.tags.length === 0 &&
    q.filmTitle.trim() === '' &&
    q.yearMin.trim() === '' &&
    q.yearMax.trim() === '' &&
    q.company === '' &&
    q.moodBefore === '' &&
    q.moodAfter === '' &&
    !q.favoritesOnly &&
    q.categoryId.trim() === '' &&
    q.completedOn.trim() === ''
  )
}

export function ratedCardsQueryKey(q: RatedCardsListQuery): string {
  return JSON.stringify({
    sort: q.sort,
    tags: [...q.tags].sort(),
    ft: q.filmTitle.trim(),
    ym: q.yearMin.trim(),
    yx: q.yearMax.trim(),
    co: q.company,
    mb: q.moodBefore,
    ma: q.moodAfter,
    fav: q.favoritesOnly,
    shelf: q.categoryId.trim(),
    completed: q.completedOn.trim(),
  })
}

function parseProfileCardsSort(value: string | null): ProfileCardsSort {
  if (value != null && PROFILE_CARDS_SORTS.includes(value as ProfileCardsSort)) {
    return value as ProfileCardsSort
  }
  return DEFAULT_RATED_CARDS_QUERY.sort
}

function parseCardCompany(value: string | null): CardCompany | '' {
  if (value != null && CARD_COMPANIES.includes(value as CardCompany)) {
    return value as CardCompany
  }
  return ''
}

function parseCardMoodBefore(value: string | null): CardMoodBefore | '' {
  if (value != null && CARD_MOODS_BEFORE.includes(value as CardMoodBefore)) {
    return value as CardMoodBefore
  }
  return ''
}

function parseCardMoodAfter(value: string | null): CardMoodAfter | '' {
  if (value != null && CARD_MOODS_AFTER.includes(value as CardMoodAfter)) {
    return value as CardMoodAfter
  }
  return ''
}

function parseTagsParam(value: string | null): string[] {
  if (value == null || value.trim() === '') {
    return []
  }
  return value
    .split(',')
    .map((tag) => tag.trim())
    .filter((tag) => tag !== '')
}

function parseFavoritesOnlyParam(value: string | null): boolean {
  return value === '1' || value === 'true'
}

export function ratedCardsQueryToSearchParams(query: RatedCardsListQuery): URLSearchParams {
  const params = new URLSearchParams()

  if (query.sort !== DEFAULT_RATED_CARDS_QUERY.sort) {
    params.set('sort', query.sort)
  }
  if (query.tags.length > 0) {
    params.set('tags', query.tags.join(','))
  }
  const filmTitle = query.filmTitle.trim()
  if (filmTitle !== '') {
    params.set('filmTitle', filmTitle)
  }
  const yearMin = query.yearMin.trim()
  if (yearMin !== '') {
    params.set('yearMin', yearMin)
  }
  const yearMax = query.yearMax.trim()
  if (yearMax !== '') {
    params.set('yearMax', yearMax)
  }
  if (query.company !== '') {
    params.set('company', query.company)
  }
  if (query.moodBefore !== '') {
    params.set('moodBefore', query.moodBefore)
  }
  if (query.moodAfter !== '') {
    params.set('moodAfter', query.moodAfter)
  }
  if (query.favoritesOnly) {
    params.set('favoritesOnly', '1')
  }
  const categoryId = query.categoryId.trim()
  if (categoryId !== '') {
    params.set('categoryId', categoryId)
  }
  const completedOn = query.completedOn.trim()
  if (completedOn !== '') {
    params.set('completedOn', completedOn)
  }

  return params
}

export function ratedCardsQueryFromSearchParams(searchParams: URLSearchParams): RatedCardsListQuery {
  return {
    sort: parseProfileCardsSort(searchParams.get('sort')),
    tags: parseTagsParam(searchParams.get('tags')),
    filmTitle: searchParams.get('filmTitle') ?? '',
    yearMin: searchParams.get('yearMin') ?? '',
    yearMax: searchParams.get('yearMax') ?? '',
    company: parseCardCompany(searchParams.get('company')),
    moodBefore: parseCardMoodBefore(searchParams.get('moodBefore')),
    moodAfter: parseCardMoodAfter(searchParams.get('moodAfter')),
    favoritesOnly: parseFavoritesOnlyParam(searchParams.get('favoritesOnly')),
    categoryId: searchParams.get('categoryId') ?? '',
    completedOn: searchParams.get('completedOn') ?? '',
  }
}

export function mergeRatedCardsFilterSearchParams(
  existing: URLSearchParams,
  filterParams: URLSearchParams,
): URLSearchParams {
  const merged = new URLSearchParams(existing)
  for (const key of RATED_CARDS_FILTER_PARAM_KEYS) {
    merged.delete(key)
  }
  filterParams.forEach((value, key) => {
    merged.set(key, value)
  })
  return merged
}

export function ratedCardsToListParams(q: RatedCardsListQuery): Omit<GetUserCardsParams, 'cursor' | 'limit'> {
  const ymn = q.yearMin.trim()
  const ymx = q.yearMax.trim()
  const yearMin = ymn === '' ? null : Number(ymn)
  const yearMax = ymx === '' ? null : Number(ymx)
  const ft = q.filmTitle.trim()
  const cs = q.categoryId.trim()
  const categoryNum = cs === '' ? null : Number(cs)
  const categoryId =
    categoryNum != null && Number.isInteger(categoryNum) && categoryNum >= 1 ? categoryNum : null

  return {
    sort: q.sort,
    ...(q.favoritesOnly ? { favoritesOnly: true as const } : {}),
    tags: q.tags.length > 0 ? q.tags : undefined,
    filmTitle: ft === '' ? null : ft,
    yearMin: yearMin != null && Number.isFinite(yearMin) ? yearMin : null,
    yearMax: yearMax != null && Number.isFinite(yearMax) ? yearMax : null,
    company: q.company === '' ? null : q.company,
    moodBefore: q.moodBefore === '' ? null : q.moodBefore,
    moodAfter: q.moodAfter === '' ? null : q.moodAfter,
    categoryId,
    completedOn: q.completedOn.trim() === '' ? null : q.completedOn.trim(),
  }
}
