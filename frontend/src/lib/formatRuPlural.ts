function ruPluralForm(count: number, one: string, few: string, many: string): string {
  return count === 1 ? one : count < 5 ? few : many
}

export function formatFilmsCount(count: number): string {
  return `${count} ${ruPluralForm(count, 'фильм', 'фильма', 'фильмов')}`
}

export function formatRatingsCount(count: number): string {
  return `${count} ${ruPluralForm(count, 'оценка', 'оценки', 'оценок')}`
}

export function formatDaysCount(count: number): string {
  return `${count} ${ruPluralForm(count, 'день', 'дня', 'дней')}`
}
