import type { MovieCard } from '../../api/profileTypes'
import type { ShelfPhysics } from '../../api/gamificationTypes'

/** Client-side fallback when gamification API is unavailable. */
export function computeShelfPhysicsFromCards(cards: readonly MovieCard[]): ShelfPhysics {
  const recent = cards.slice(0, 5)
  let streakLow = 0
  let streakHigh = 0

  for (const card of recent) {
    if (card.rating <= 3) {
      streakLow += 1
      streakHigh = 0
    } else if (card.rating >= 9) {
      streakHigh += 1
      streakLow = 0
    } else {
      streakLow = 0
      streakHigh = 0
    }
  }

  if (streakLow >= 3) {
    return { mode: 'slump', streak_length: streakLow }
  }
  if (streakHigh >= 3) {
    return { mode: 'glow', streak_length: streakHigh }
  }
  return { mode: 'neutral', streak_length: 0 }
}
