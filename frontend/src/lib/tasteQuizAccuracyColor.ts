/** Returns hex color for taste-quiz accuracy percentage badge digits. */
export function tasteQuizAccuracyColor(accuracyPct: number): string {
  const pct = Math.max(0, Math.min(100, Math.round(accuracyPct)))
  if (pct <= 29) return '#ff7a8c'
  if (pct <= 59) return '#e8b86d'
  if (pct <= 84) return '#86efac'
  return '#5eead4'
}
