import { lazy, Suspense } from 'react'

import type { MarathonAchievement } from '../../api/gamificationTypes'
import type { RatedCardsListQuery } from '../../lib/ratedCardsListQuery'
import { InlineLoadingState } from '../ui/InlineLoadingState'

const ProfileStatsPanel = lazy(() =>
  import('./ProfileStatsPanel').then((m) => ({ default: m.ProfileStatsPanel })),
)

type ProfileStatsTabProps = {
  userId: string
  cardsQuery: RatedCardsListQuery
  onCardsQueryChange: (next: RatedCardsListQuery) => void
  enableCategoryFilter?: boolean
  showTasteQuizTeaser?: boolean
  showPassportCollection?: boolean
  showAchievements?: boolean
  onMarathonDrill?: (marathon: MarathonAchievement) => void
  onDrillToRatedCards?: () => void
  className?: string
}

export function ProfileStatsTab({
  userId,
  cardsQuery,
  onCardsQueryChange,
  enableCategoryFilter,
  showTasteQuizTeaser,
  showPassportCollection,
  showAchievements,
  onMarathonDrill,
  onDrillToRatedCards,
  className,
}: ProfileStatsTabProps) {
  return (
    <div className={className}>
      <Suspense fallback={<InlineLoadingState message="Загрузка статистики…" />}>
        <ProfileStatsPanel
          userId={userId}
          cardsQuery={cardsQuery}
          onCardsQueryChange={onCardsQueryChange}
          enableCategoryFilter={enableCategoryFilter}
          showTasteQuizTeaser={showTasteQuizTeaser}
          showPassportCollection={showPassportCollection}
          showAchievements={showAchievements}
          onMarathonDrill={onMarathonDrill}
          onDrillToRatedCards={onDrillToRatedCards}
        />
      </Suspense>
    </div>
  )
}
