export type FilmAwardBadgeLike = {
  kind: 'oscar_best_picture_nominee' | 'oscar_best_picture_winner'
  ceremony_year: number
}

function oscarRoleLabel(kind: FilmAwardBadgeLike['kind']): string {
  return kind === 'oscar_best_picture_winner'
    ? 'Оскар — лучший фильм (победитель)'
    : 'Оскар — лучший фильм (номинант)'
}

/** Prefer winner, then newest ceremony year — for compact feed UI. */
export function primaryFilmAwardBadge(
  badges: FilmAwardBadgeLike[] | null | undefined,
): FilmAwardBadgeLike | null {
  if (badges == null || badges.length === 0) return null
  const sorted = [...badges].sort((a, b) => {
    const aWin = a.kind === 'oscar_best_picture_winner' ? 0 : 1
    const bWin = b.kind === 'oscar_best_picture_winner' ? 0 : 1
    if (aWin !== bWin) return aWin - bWin
    return b.ceremony_year - a.ceremony_year
  })
  return sorted[0] ?? null
}

export function releaseYearLabel(releaseYear: number | null | undefined): string {
  if (releaseYear == null) return '—'
  return String(releaseYear)
}

export function oscarBadgeTitle(
  badge: FilmAwardBadgeLike,
  releaseYear: number | null | undefined,
): string {
  const yearText = releaseYear != null ? String(releaseYear) : 'год неизвестен'
  return `${oscarRoleLabel(badge.kind)}, ${yearText} (церемония ${badge.ceremony_year})`
}

export function oscarBadgeAriaLabel(
  badge: FilmAwardBadgeLike,
  releaseYear: number | null | undefined,
): string {
  return oscarBadgeTitle(badge, releaseYear)
}

export function isOscarWinnerBadge(badge: FilmAwardBadgeLike): boolean {
  return badge.kind === 'oscar_best_picture_winner'
}
