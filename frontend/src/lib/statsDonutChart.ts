export type DonutSegmentInput = {
  label: string
  count: number
  color: string
  value?: string
}

export type DecadeBucket = {
  label: string
  decadeStart: number
  decadeEnd: number
  count: number
  value: string
}

export type PeakRatedYear = {
  year: number
  count: number
}

/** Build a CSS `conic-gradient(...)` from segment counts and colors. Skips zero-count segments. */
export function buildConicGradient(segments: readonly { count: number; color: string }[]): string {
  const total = segments.reduce((acc, segment) => acc + segment.count, 0)
  if (total <= 0) {
    return 'conic-gradient(transparent 0% 100%)'
  }

  let cumulative = 0
  const stops: string[] = []
  for (const segment of segments) {
    if (segment.count <= 0) continue
    const startPct = (cumulative / total) * 100
    cumulative += segment.count
    const endPct = (cumulative / total) * 100
    stops.push(`${segment.color} ${startPct}% ${endPct}%`)
  }

  if (stops.length === 0) {
    return 'conic-gradient(transparent 0% 100%)'
  }

  return `conic-gradient(${stops.join(', ')})`
}

export function aggregateYearDistributionToDecades(
  yearDistribution: readonly { year: number; count: number }[],
): DecadeBucket[] {
  const byDecade = new Map<number, number>()
  for (const item of yearDistribution) {
    if (item.count <= 0) continue
    const decadeStart = Math.floor(item.year / 10) * 10
    byDecade.set(decadeStart, (byDecade.get(decadeStart) ?? 0) + item.count)
  }

  return [...byDecade.entries()]
    .sort(([a], [b]) => a - b)
    .map(([decadeStart, count]) => ({
      label: `${decadeStart}-е`,
      decadeStart,
      decadeEnd: decadeStart + 9,
      count,
      value: String(decadeStart),
    }))
}

export function findPeakRatedYear(
  ratedYearDistribution: readonly { year: number; count: number }[] | undefined,
): PeakRatedYear | null {
  if (ratedYearDistribution == null || ratedYearDistribution.length === 0) {
    return null
  }

  let peak: PeakRatedYear | null = null
  for (const item of ratedYearDistribution) {
    if (item.count <= 0) continue
    if (peak == null || item.count > peak.count || (item.count === peak.count && item.year > peak.year)) {
      peak = { year: item.year, count: item.count }
    }
  }

  return peak
}

/** Distinct hues for rating buckets 1–10 (low → high). */
export const RATING_DONUT_COLORS: readonly string[] = [
  '#ef7d9b',
  '#f089a8',
  '#f59e0b',
  '#e8b86d',
  '#94a3b8',
  '#64748b',
  '#4f87ff',
  '#6366f1',
  '#5de1d4',
  '#34d399',
]

export const COMPANY_DONUT_COLORS: readonly string[] = ['#5de1d4', '#4f87ff', '#e8b86d', '#ef7d9b']

export const MOOD_AFTER_DONUT_COLORS: readonly string[] = [
  '#e8b86d',
  '#4f87ff',
  '#5de1d4',
  '#94a3b8',
  '#ef7d9b',
]

export const SHELF_DONUT_COLORS: readonly string[] = [
  '#5de1d4',
  '#4f87ff',
  '#e8b86d',
  '#ef7d9b',
  '#6366f1',
  '#34d399',
  '#f59e0b',
  '#94a3b8',
]

export const DECADE_DONUT_COLORS: readonly string[] = [
  '#64748b',
  '#94a3b8',
  '#4f87ff',
  '#5de1d4',
  '#e8b86d',
  '#ef7d9b',
  '#6366f1',
  '#34d399',
]
