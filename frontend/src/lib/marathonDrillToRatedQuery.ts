import type { MarathonAchievement } from '../api/gamificationTypes'
import { DEFAULT_RATED_CARDS_QUERY, type RatedCardsListQuery } from './ratedCardsListQuery'

/** Applies marathon chip drill-down to rated-cards filters (director/franchise, not title search). */
export function marathonDrillToRatedQuery(
  current: RatedCardsListQuery,
  marathon: MarathonAchievement,
): RatedCardsListQuery {
  if (marathon.kind === 'director') {
    const parsed = Number.parseInt(marathon.key, 10)
    const directorKinopoiskId =
      Number.isInteger(parsed) && parsed >= 1 ? String(parsed) : marathon.key.trim()
    return {
      ...current,
      directorKinopoiskId,
      actorKinopoiskId: '',
      franchiseKey: '',
      filmTitle: '',
    }
  }

  if (marathon.kind === 'franchise') {
    return {
      ...current,
      franchiseKey: marathon.key.trim(),
      directorKinopoiskId: '',
      actorKinopoiskId: '',
      filmTitle: '',
    }
  }

  return {
    ...current,
    filmTitle: marathon.label.trim(),
  }
}

export function isMarathonDrillQuery(next: RatedCardsListQuery): boolean {
  return (
    next.directorKinopoiskId.trim() !== '' ||
    next.actorKinopoiskId.trim() !== '' ||
    next.franchiseKey.trim() !== '' ||
    (next.filmTitle.trim() !== '' && next.filmTitle !== DEFAULT_RATED_CARDS_QUERY.filmTitle)
  )
}
