import { Avatar, Title } from '@telegram-apps/telegram-ui'

import type { PublicProfile } from '../../api/profileTypes'
import type { StreakBatchItem } from '../../api/streaksTypes'
import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import type { WatchingNowBatchItem } from '../../api/watchPartyTypes'
import { displayNameFromProfile, profileInitials } from '../../lib/profileDisplay'
import { RatingStreakAuthorBadge } from '../streaks/RatingStreakAuthorBadge'
import { TasteQuizCommentAuthorBadge } from '../tasteQuiz/TasteQuizCommentAuthorBadge'
import { WatchingNowAuthorBadge } from '../watchparty/WatchingNowAuthorBadge'
import { ProfileCompactMetrics, type ProfileCompactMetricsProps } from './ProfileCompactMetrics'

type ProfileHeaderProps = {
  profile: PublicProfile
  subtitle?: string
  viewerId?: string | null
  knowledgeByOwnerId?: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId?: Record<string, StreakBatchItem>
  watchingByUserId?: Record<string, WatchingNowBatchItem>
  showTasteQuizBadge?: boolean
  metrics?: ProfileCompactMetricsProps
  avatarSize?: number
  className?: string
}

export function ProfileHeader({
  profile,
  subtitle,
  viewerId = null,
  knowledgeByOwnerId = {},
  streakByUserId = {},
  watchingByUserId = {},
  showTasteQuizBadge = true,
  metrics,
  avatarSize = 76,
  className = '',
}: ProfileHeaderProps) {
  const name = displayNameFromProfile(profile)

  return (
    <div className={`flex items-start gap-3.5 py-2 ${className}`.trim()}>
      <div className="shrink-0">
        <Avatar
          src={profile.photo_url ?? undefined}
          acronym={profileInitials(profile)}
          size={avatarSize}
        />
      </div>
      <div className="min-w-0 flex-1 text-left">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
          <Title level="2" weight="2">
            {name}
          </Title>
          {showTasteQuizBadge ? (
            <TasteQuizCommentAuthorBadge
              knowledgeByAuthor={knowledgeByOwnerId}
              authorId={profile.id}
              viewerId={viewerId}
            />
          ) : null}
          <RatingStreakAuthorBadge streakByUserId={streakByUserId} authorId={profile.id} />
          <WatchingNowAuthorBadge watchingByUserId={watchingByUserId} authorId={profile.id} />
        </div>
        {subtitle != null && subtitle !== '' ? (
          <p className="filmony-text-panel mt-1 max-w-full text-sm text-(--tgui--hint_color,#94a3b8)">{subtitle}</p>
        ) : null}
        <p className="mt-0.5 font-mono text-xs text-(--tgui--hint_color,#94a3b8)">@{profile.profile_slug}</p>
        {metrics != null ? <ProfileCompactMetrics {...metrics} /> : null}
      </div>
    </div>
  )
}
