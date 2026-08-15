import { useUserActivityHeatmapQuery } from '../../hooks/useUserActivityHeatmapQuery'

import { ProfileActivityHeatmap } from './ProfileActivityHeatmap'

export type ProfileActivityHeatmapSectionProps = {
  userId: string
  onDaySelect: (isoDate: string) => void
  className?: string
}

export function ProfileActivityHeatmapSection({
  userId,
  onDaySelect,
  className,
}: ProfileActivityHeatmapSectionProps) {
  const heatmapQuery = useUserActivityHeatmapQuery(userId, null, {
    enabled: userId.trim() !== '',
  })
  const heatmap = heatmapQuery.data ?? null
  const loading = heatmapQuery.isPending && heatmap == null
  const activityLoading = heatmapQuery.isFetching && heatmap != null

  if (userId.trim() === '') {
    return null
  }

  if (heatmapQuery.isError && heatmap == null) {
    return null
  }

  if (loading && heatmap == null) {
    return (
      <div className={className}>
        <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-3 text-center">
          <p className="text-sm text-(--tgui--hint_color)">Загрузка активности…</p>
        </div>
      </div>
    )
  }

  if (heatmap == null) {
    return null
  }

  return (
    <div className={className}>
      <ProfileActivityHeatmap
        activity={heatmap.activity_distribution}
        activityStart={heatmap.activity_start}
        activityEnd={heatmap.activity_end}
        loading={activityLoading}
        onDaySelect={onDaySelect}
      />
    </div>
  )
}
