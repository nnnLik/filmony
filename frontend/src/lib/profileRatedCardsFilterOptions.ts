import type { ProfileCardsSort } from '../api/profileApi'
import type { CardCompany, CardMoodAfter, CardMoodBefore } from '../api/profileTypes'

export const PROFILE_RATED_CARDS_SORT_OPTIONS: Array<{ value: ProfileCardsSort; label: string }> = [
  { value: 'recent', label: 'Сначала новые' },
  { value: 'rating_desc', label: 'Оценка: выше' },
  { value: 'rating_asc', label: 'Оценка: ниже' },
]

export function profileRatedCardsSortLabel(sort: ProfileCardsSort): string {
  return PROFILE_RATED_CARDS_SORT_OPTIONS.find((o) => o.value === sort)?.label ?? sort
}

export const PROFILE_RATED_COMPANY_OPTIONS: Array<{ value: CardCompany | ''; label: string }> = [
  { value: '', label: 'Кто угодно' },
  { value: 'alone', label: 'Один' },
  { value: 'partner', label: 'С партнёром' },
  { value: 'friends', label: 'С друзьями' },
  { value: 'family', label: 'С семьёй' },
]

export const PROFILE_RATED_MOOD_BEFORE_OPTIONS: Array<{ value: CardMoodBefore | ''; label: string }> = [
  { value: '', label: 'Любое' },
  { value: 'relax', label: 'Расслабиться' },
  { value: 'laugh', label: 'Поржать' },
  { value: 'sad', label: 'Погрустить' },
  { value: 'thrill', label: 'Напряжение' },
]

export const PROFILE_RATED_MOOD_AFTER_OPTIONS: Array<{ value: CardMoodAfter | ''; label: string }> = [
  { value: '', label: 'Любой итог' },
  { value: 'laughed', label: 'Весёлый' },
  { value: 'cried', label: 'Плакал' },
  { value: 'enjoyed', label: 'Кайфанул' },
  { value: 'tense', label: 'Уставший' },
  { value: 'wasted_time', label: 'Зря время' },
]

/** Shared native control styling for filter selects/inputs */
export const PROFILE_RATED_FILTERS_NATIVE_CONTROL_CLASS =
  'min-w-0 w-full rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) px-2.5 py-2 text-sm text-(--tgui--text_color) outline-none ring-(--tgui--link_color) focus-visible:ring-2'
