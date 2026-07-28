/** Maps streak length to visual heat in [0, 1]; caps at 10 days. */
export function streakHeat(current: number): number {
  if (current <= 3) return 0
  return Math.min(1, Math.max(0, (current - 3) / 7))
}
