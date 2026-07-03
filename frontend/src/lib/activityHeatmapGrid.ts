export type ActivityBucket = {
  date: string
  count: number
}

export type HeatmapCell = {
  date: string
  count: number
  level: 0 | 1 | 2 | 3 | 4
  weekIndex: number
  dayIndex: number
  inRange: boolean
}

const DAY_MS = 86_400_000

function parseIsoDate(value: string): Date {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day))
}

function formatIsoDate(date: Date): string {
  return date.toISOString().slice(0, 10)
}

function mondayAlignedStart(date: Date): Date {
  const aligned = new Date(date)
  const dow = aligned.getUTCDay()
  const offset = dow === 0 ? -6 : 1 - dow
  aligned.setUTCDate(aligned.getUTCDate() + offset)
  return aligned
}

function sundayAlignedEnd(date: Date): Date {
  const aligned = new Date(date)
  const dow = aligned.getUTCDay()
  const offset = dow === 0 ? 0 : 7 - dow
  aligned.setUTCDate(aligned.getUTCDate() + offset)
  return aligned
}

export function countToHeatLevel(count: number, maxCount: number): 0 | 1 | 2 | 3 | 4 {
  if (count <= 0) return 0
  if (maxCount <= 1) return 1
  const ratio = count / maxCount
  if (ratio <= 0.25) return 1
  if (ratio <= 0.5) return 2
  if (ratio <= 0.75) return 3
  return 4
}

/** Builds a GitHub-style grid: 7 weekday rows × week columns (Mon-first). */
export function buildActivityHeatmapGrid(
  buckets: ActivityBucket[],
  activityStart: string,
  activityEnd: string,
): HeatmapCell[][] {
  const countByDate = new Map(buckets.map((bucket) => [bucket.date, bucket.count]))
  const maxCount = Math.max(1, ...buckets.map((bucket) => bucket.count), 0)

  const rangeStart = parseIsoDate(activityStart)
  const rangeEnd = parseIsoDate(activityEnd)
  const gridStart = mondayAlignedStart(rangeStart)
  const gridEnd = sundayAlignedEnd(rangeEnd)

  const weekCount =
    Math.floor((gridEnd.getTime() - gridStart.getTime()) / (7 * DAY_MS)) + 1
  const rows: HeatmapCell[][] = Array.from({ length: 7 }, () =>
    Array.from({ length: weekCount }, (_, weekIndex) => ({
      date: '',
      count: 0,
      level: 0 as const,
      weekIndex,
      dayIndex: 0,
      inRange: false,
    })),
  )

  let cursor = new Date(gridStart)
  for (let weekIndex = 0; weekIndex < weekCount; weekIndex += 1) {
    for (let dayIndex = 0; dayIndex < 7; dayIndex += 1) {
      const dateStr = formatIsoDate(cursor)
      const inRange = cursor >= rangeStart && cursor <= rangeEnd
      const count = inRange ? (countByDate.get(dateStr) ?? 0) : 0
      rows[dayIndex][weekIndex] = {
        date: dateStr,
        count,
        level: inRange ? countToHeatLevel(count, maxCount) : 0,
        weekIndex,
        dayIndex,
        inRange,
      }
      cursor = new Date(cursor.getTime() + DAY_MS)
    }
  }

  return rows
}

export function sumActivityCounts(buckets: ActivityBucket[]): number {
  return buckets.reduce((acc, bucket) => acc + bucket.count, 0)
}

export function formatActivityDayLabel(isoDate: string): string {
  const date = parseIsoDate(isoDate)
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(date)
}
