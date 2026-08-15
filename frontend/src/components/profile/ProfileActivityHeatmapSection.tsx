import { useEffect, useMemo, useState } from 'react'

import { useUserMovieCardStatsQuery } from '../../hooks/useUserMovieCardStatsQuery'

import { ProfileActivityHeatmap } from './ProfileActivityHeatmap'

export type ProfileActivityHeatmapSectionProps = {
  userId: string
  onDaySelect: (isoDate: string, shelfId: string) => void
  className?: string
}

export function ProfileActivityHeatmapSection({
  userId,
  onDaySelect,
  className,
}: ProfileActivityHeatmapSectionProps) {
  const [activityShelfId, setActivityShelfId] = useState('')

  const activityCategoryId = useMemo(() => {
    if (activityShelfId === '') {
      return null
    }
    const shelfNum = Number(activityShelfId)
    return Number.isInteger(shelfNum) && shelfNum >= 1 ? shelfNum : null
  }, [activityShelfId])

  const statsQuery = useUserMovieCardStatsQuery(userId, activityCategoryId, {
    enabled: userId.trim() !== '',
  })
  const stats = statsQuery.data ?? null
  const loading = statsQuery.isPending && stats == null
  const activityLoading = statsQuery.isFetching && stats != null

  useEffect(() => {
    queueMicrotask(() => {
      setActivityShelfId('')
    })
  }, [userId])

  const shelfDistributionRows = useMemo(
    () => (stats?.category_distribution ?? []).filter((row) => row.count > 0),
    [stats?.category_distribution],
  )

  if (userId.trim() === '') {
    return null
  }

  if (statsQuery.isError && stats == null) {
    return null
  }

  if (loading && stats == null) {
    return (
      <div className={className}>
        <div className="rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-6 text-center">
          <p className="text-sm text-(--tgui--hint_color)">Загрузка активности…</p>
        </div>
      </div>
    )
  }

  if (stats == null) {
    return null
  }

  return (
    <div className={className}>
      <ProfileActivityHeatmap
        activity={stats.activity_distribution}
        activityStart={stats.activity_start}
        activityEnd={stats.activity_end}
        shelves={shelfDistributionRows}
        selectedShelfId={activityShelfId}
        onShelfChange={setActivityShelfId}
        loading={activityLoading}
        onDaySelect={onDaySelect}
      />
    </div>
  )
}
