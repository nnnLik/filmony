export function ratingPalette(value: number): { ring: string; glow: string; text: string } {
  if (value <= 3) return { ring: '#ef4444', glow: 'rgba(239,68,68,0.35)', text: '#fca5a5' }
  if (value <= 5) return { ring: '#f59e0b', glow: 'rgba(245,158,11,0.35)', text: '#fcd34d' }
  if (value <= 7) return { ring: '#84cc16', glow: 'rgba(132,204,22,0.35)', text: '#bef264' }
  return { ring: '#22c55e', glow: 'rgba(34,197,94,0.35)', text: '#86efac' }
}

export function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}
