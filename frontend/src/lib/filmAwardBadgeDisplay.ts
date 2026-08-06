export type FilmAwardBadgeLike = {
  kind: 'oscar_best_picture_nominee' | 'oscar_best_picture_winner'
  ceremony_year: number
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
