import type { UserCollectionProgress } from '../../api/collectionsTypes'
import { collectionProgressPercent } from '../../lib/collectionProgress'

type CollectionProgressBarProps = {
  progress: UserCollectionProgress | null | undefined
  className?: string
}

function progressPercent(progress: UserCollectionProgress | null | undefined): number {
  return collectionProgressPercent(progress) ?? 0
}

export function CollectionProgressBar({ progress, className }: CollectionProgressBarProps) {
  if (progress == null) {
    return null
  }

  const rated = progress.rated_count
  const total = progress.total_count
  const percent = progressPercent(progress)

  return (
    <div className={className}>
      <div className="flex items-center justify-between gap-2 text-xs text-(--tgui--hint_color)">
        <span className="tabular-nums">
          {rated} / {total}
        </span>
        <span className="tabular-nums font-medium text-(--tgui--text_color)">{percent}%</span>
      </div>
      <div
        className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-(--tgui--secondary_bg_color)"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Прогресс: ${rated} из ${total}`}
      >
        <div
          className="h-full rounded-full bg-(--tgui--link_color) transition-[width]"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  )
}
