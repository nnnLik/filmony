export function hasMeaningfulCardRating(card: { is_planned?: boolean; rating: number }): boolean {
  return card.is_planned !== true && card.rating >= 1
}

export type RatingPalette = {
  ring: string
  glow: string
  text: string
  track: string
}

export function ratingPalette(value: number): RatingPalette {
  if (value <= 3) {
    return { ring: '#ef4444', glow: 'rgba(239,68,68,0.35)', text: '#fca5a5', track: 'rgba(239,68,68,0.15)' }
  }
  if (value <= 5) {
    return { ring: '#f59e0b', glow: 'rgba(245,158,11,0.32)', text: '#fcd34d', track: 'rgba(245,158,11,0.14)' }
  }
  if (value <= 7) {
    return { ring: '#84cc16', glow: 'rgba(132,204,22,0.3)', text: '#bef264', track: 'rgba(132,204,22,0.12)' }
  }
  return { ring: '#22c55e', glow: 'rgba(34,197,94,0.32)', text: '#86efac', track: 'rgba(34,197,94,0.12)' }
}

export function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

/** Доля окружности (0–1) для шкалы 1–10 */
export function ratingDashOffset(value: number): number {
  const clamped = Math.min(10, Math.max(1, value))
  const p = (clamped - 1) / 9
  return 219.99 * (1 - p)
}
