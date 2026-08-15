import { useMemo, useState } from 'react'

import type { ActivityDistributionItem } from '../../api/profileTypes'
import {
  buildActivityHeatmapGrid,
  clipHeatmapWindow,
  formatActivityDayLabel,
} from '../../lib/activityHeatmapGrid'

const WEEKDAY_LABELS = ['Пн', '', 'Ср', '', 'Пт', '', ''] as const

const LEVEL_CLASS: Record<0 | 1 | 2 | 3 | 4, string> = {
  0: 'bg-[color-mix(in_srgb,var(--tgui--hint_color)_10%,transparent)]',
  1: 'bg-[color-mix(in_srgb,var(--tgui--link_color)_22%,transparent)]',
  2: 'bg-[color-mix(in_srgb,var(--tgui--link_color)_40%,transparent)]',
  3: 'bg-[color-mix(in_srgb,var(--tgui--link_color)_62%,transparent)]',
  4: 'bg-[color-mix(in_srgb,var(--tgui--link_color)_88%,transparent)]',
}

type ProfileActivityHeatmapProps = {
  activity: ActivityDistributionItem[]
  activityStart: string
  activityEnd: string
  loading?: boolean
  onDaySelect?: (isoDate: string) => void
}

function formatCompletedCount(count: number): string {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod100 >= 11 && mod100 <= 14) {
    return `${count} просмотров`
  }
  if (mod10 === 1) {
    return `${count} просмотр`
  }
  if (mod10 >= 2 && mod10 <= 4) {
    return `${count} просмотра`
  }
  return `${count} просмотров`
}

function formatDayHint(isoDate: string, count: number): string {
  return `${formatActivityDayLabel(isoDate)} · ${formatCompletedCount(count)}`
}

export function ProfileActivityHeatmap({
  activity,
  activityStart,
  activityEnd,
  loading = false,
  onDaySelect,
}: ProfileActivityHeatmapProps) {
  const [hoveredDate, setHoveredDate] = useState<string | null>(null)

  const clippedWindow = useMemo(
    () => clipHeatmapWindow(activityStart, activityEnd),
    [activityStart, activityEnd],
  )

  const grid = useMemo(
    () =>
      buildActivityHeatmapGrid(
        activity,
        clippedWindow.start,
        clippedWindow.end,
      ),
    [activity, clippedWindow],
  )
  const weekCount = grid[0]?.length ?? 0
  const totalCompleted = useMemo(
    () =>
      activity.reduce(
        (acc, bucket) =>
          bucket.date >= clippedWindow.start && bucket.date <= clippedWindow.end
            ? acc + bucket.count
            : acc,
        0,
      ),
    [activity, clippedWindow],
  )

  const hoveredCell = useMemo(() => {
    if (hoveredDate == null) return null
    for (const row of grid) {
      for (const cell of row) {
        if (cell.inRange && cell.date === hoveredDate) {
          return cell
        }
      }
    }
    return null
  }, [grid, hoveredDate])

  const handleCellActivate = (isoDate: string, count: number, inRange: boolean) => {
    if (!inRange || count <= 0) return
    onDaySelect?.(isoDate)
  }

  return (
    <section className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2.5 py-2">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-xs font-medium text-(--tgui--text_color)">
          Активность просмотров
        </h3>
        <p className="flex items-center gap-1.5 text-[11px] text-(--tgui--hint_color)">
          <span>
            {totalCompleted > 0 ? `${totalCompleted} за месяц` : 'Нет просмотров'}
          </span>
          {loading ? <span>Обновление…</span> : null}
        </p>
      </div>

      <div className="mt-1.5 flex justify-center gap-1.5">
        <div className="grid shrink-0 grid-rows-7 gap-[2px] text-[9px] leading-none text-(--tgui--hint_color)">
          {WEEKDAY_LABELS.map((label, index) => (
            <span key={`wd-${index}`} className="flex h-[10px] items-center">
              {label}
            </span>
          ))}
        </div>
        <div
          className="grid shrink-0 gap-[2px]"
          style={{
            gridTemplateRows: 'repeat(7, 10px)',
            gridTemplateColumns: `repeat(${weekCount}, 10px)`,
          }}
          role="grid"
          aria-label="Сетка активности просмотров за последний месяц"
        >
          {grid.flatMap((row) =>
            row.map((cell) => {
              const dayHint = cell.inRange
                ? formatDayHint(cell.date, cell.count)
                : undefined
              return (
                <button
                  key={`${cell.weekIndex}-${cell.dayIndex}`}
                  type="button"
                  role="gridcell"
                  disabled={!cell.inRange}
                  title={dayHint}
                  aria-label={dayHint}
                  className={`size-2.5 rounded-[2px] border border-transparent outline-none transition-[transform,opacity] focus-visible:ring-1 focus-visible:ring-(--tgui--link_color) disabled:cursor-default ${
                    LEVEL_CLASS[cell.level]
                  } ${hoveredDate === cell.date ? 'ring-1 ring-(--tgui--link_color)' : ''} ${
                    cell.inRange && cell.count > 0 ? 'cursor-pointer active:scale-95' : ''
                  }`}
                  onMouseEnter={() => {
                    if (cell.inRange) setHoveredDate(cell.date)
                  }}
                  onMouseLeave={() => setHoveredDate(null)}
                  onFocus={() => {
                    if (cell.inRange) setHoveredDate(cell.date)
                  }}
                  onBlur={() => setHoveredDate(null)}
                  onClick={() => handleCellActivate(cell.date, cell.count, cell.inRange)}
                />
              )
            }),
          )}
        </div>
      </div>

      <div className="mt-1.5 flex items-center justify-between gap-2">
        <p className="min-h-[1rem] tabular-nums text-[11px] text-(--tgui--hint_color)">
          {hoveredCell
            ? formatDayHint(hoveredCell.date, hoveredCell.count)
            : '\u00a0'}
        </p>
        <div className="flex items-center gap-1 text-[10px] text-(--tgui--hint_color)">
          <span>Меньше</span>
          {[0, 1, 2, 3, 4].map((level) => (
            <span
              key={level}
              className={`size-2.5 rounded-[2px] ${LEVEL_CLASS[level as 0 | 1 | 2 | 3 | 4]}`}
            />
          ))}
          <span>Больше</span>
        </div>
      </div>
    </section>
  )
}
