import { useMemo, useState } from 'react'

import type { ActivityDistributionItem, CategoryDistributionItem } from '../../api/profileTypes'
import {
  buildActivityHeatmapGrid,
  formatActivityDayLabel,
  sumActivityCounts,
} from '../../lib/activityHeatmapGrid'

import { ProfileStatsSectionCard } from './ProfileStatsSummaryCard'

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
  shelves: CategoryDistributionItem[]
  selectedShelfId: string
  onShelfChange: (nextShelfId: string) => void
  loading?: boolean
  onDaySelect?: (isoDate: string, shelfId: string) => void
}

export function ProfileActivityHeatmap({
  activity,
  activityStart,
  activityEnd,
  shelves,
  selectedShelfId,
  onShelfChange,
  loading = false,
  onDaySelect,
}: ProfileActivityHeatmapProps) {
  const [focusedDate, setFocusedDate] = useState<string | null>(null)

  const grid = useMemo(
    () => buildActivityHeatmapGrid(activity, activityStart, activityEnd),
    [activity, activityStart, activityEnd],
  )
  const weekCount = grid[0]?.length ?? 0
  const totalCompleted = sumActivityCounts(activity)

  const shelfOptions = useMemo(() => {
    const items = shelves
      .filter((row) => row.category_id != null)
      .map((row) => ({
        id: String(row.category_id),
        label: row.name,
        count: row.count,
      }))
    return items
  }, [shelves])

  const handleCellActivate = (isoDate: string, count: number, inRange: boolean) => {
    if (!inRange || count <= 0) return
    setFocusedDate(isoDate)
    onDaySelect?.(isoDate, selectedShelfId)
  }

  return (
    <ProfileStatsSectionCard title="Активность просмотров">
      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs text-(--tgui--hint_color)">
            {totalCompleted > 0
              ? `${totalCompleted} завершённых за 3 месяца`
              : 'Пока нет завершённых просмотров'}
          </p>
          {loading ? (
            <span className="text-xs text-(--tgui--hint_color)">Обновление…</span>
          ) : null}
        </div>

        {shelfOptions.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              aria-pressed={selectedShelfId === ''}
              className={`rounded-lg border px-2 py-0.5 text-[11px] outline-none transition-[background-color,border-color] focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) ${
                selectedShelfId === ''
                  ? 'border-[color-mix(in_srgb,var(--tgui--link_color)_45%,transparent)] bg-[color-mix(in_srgb,var(--tgui--link_color)_14%,transparent)] text-(--tgui--text_color)'
                  : 'border-(--tgui--divider_color) bg-(--tgui--bg_color) text-(--tgui--hint_color)'
              }`}
              onClick={() => onShelfChange('')}
            >
              Все полки
            </button>
            {shelfOptions.map((shelf) => (
              <button
                key={shelf.id}
                type="button"
                aria-pressed={selectedShelfId === shelf.id}
                className={`max-w-[min(100%,10rem)] truncate rounded-lg border px-2 py-0.5 text-[11px] outline-none transition-[background-color,border-color] focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) ${
                  selectedShelfId === shelf.id
                    ? 'border-[color-mix(in_srgb,var(--tgui--link_color)_45%,transparent)] bg-[color-mix(in_srgb,var(--tgui--link_color)_14%,transparent)] text-(--tgui--text_color)'
                    : 'border-(--tgui--divider_color) bg-(--tgui--bg_color) text-(--tgui--hint_color)'
                }`}
                onClick={() => onShelfChange(shelf.id)}
              >
                {shelf.label}
              </button>
            ))}
          </div>
        ) : null}

        <div className="-mx-1 overflow-x-auto px-1 pb-1">
          <div className="inline-flex min-w-full items-start gap-2">
            <div className="grid shrink-0 grid-rows-7 gap-[3px] pt-[2px] text-[9px] leading-none text-(--tgui--hint_color)">
              {WEEKDAY_LABELS.map((label, index) => (
                <span key={`wd-${index}`} className="flex h-[11px] items-center">
                  {label}
                </span>
              ))}
            </div>
            <div
              className="grid shrink-0 gap-[3px]"
              style={{
                gridTemplateRows: 'repeat(7, 11px)',
                gridTemplateColumns: `repeat(${weekCount}, 11px)`,
              }}
              role="grid"
              aria-label="Сетка активности просмотров за 3 месяца"
            >
              {grid.flatMap((row) =>
                row.map((cell) => (
                  <button
                    key={`${cell.weekIndex}-${cell.dayIndex}`}
                    type="button"
                    role="gridcell"
                    disabled={!cell.inRange || cell.count <= 0}
                    aria-label={
                      cell.inRange
                        ? `${formatActivityDayLabel(cell.date)}: ${cell.count} просмотров`
                        : undefined
                    }
                    className={`size-[11px] rounded-[2px] border border-transparent outline-none transition-[transform,opacity] focus-visible:ring-1 focus-visible:ring-(--tgui--link_color) disabled:cursor-default sm:size-3 ${
                      LEVEL_CLASS[cell.level]
                    } ${focusedDate === cell.date ? 'ring-1 ring-(--tgui--link_color)' : ''} ${
                      cell.inRange && cell.count > 0 ? 'cursor-pointer active:scale-95' : ''
                    }`}
                    onClick={() => handleCellActivate(cell.date, cell.count, cell.inRange)}
                  />
                )),
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-1 text-[10px] text-(--tgui--hint_color)">
          <span>Меньше</span>
          {[0, 1, 2, 3, 4].map((level) => (
            <span
              key={level}
              className={`size-[11px] rounded-[2px] sm:size-3 ${LEVEL_CLASS[level as 0 | 1 | 2 | 3 | 4]}`}
            />
          ))}
          <span>Больше</span>
        </div>
      </div>
    </ProfileStatsSectionCard>
  )
}
