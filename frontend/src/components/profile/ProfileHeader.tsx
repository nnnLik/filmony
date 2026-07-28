import { Avatar, Title } from '@telegram-apps/telegram-ui'

import type { PublicProfile } from '../../api/profileTypes'
import type { StreakBatchItem } from '../../api/streaksTypes'
import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import { displayNameFromProfile, profileInitials } from '../../lib/profileDisplay'
import { RatingStreakAuthorBadge } from '../streaks/RatingStreakAuthorBadge'
import { TasteQuizCommentAuthorBadge } from '../tasteQuiz/TasteQuizCommentAuthorBadge'

type ProfileHeaderProps = {
  profile: PublicProfile
  subtitle?: string
  viewerId?: string | null
  knowledgeByOwnerId?: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId?: Record<string, StreakBatchItem>
}

export function ProfileHeader({
  profile,
  subtitle,
  viewerId = null,
  knowledgeByOwnerId = {},
  streakByUserId = {},
}: ProfileHeaderProps) {
  const name = displayNameFromProfile(profile)
  return (
    <div className="flex flex-col items-center gap-3 py-4">
      <Avatar src={profile.photo_url ?? undefined} acronym={profileInitials(profile)} size={72} />
      <div className="text-center">
        <div className="flex flex-wrap items-center justify-center gap-x-2 gap-y-0.5">
          <Title level="2" weight="2">
            {name}
          </Title>
          <TasteQuizCommentAuthorBadge
            knowledgeByAuthor={knowledgeByOwnerId}
            authorId={profile.id}
            viewerId={viewerId}
          />
          <RatingStreakAuthorBadge streakByUserId={streakByUserId} authorId={profile.id} />
        </div>
        {subtitle != null && subtitle !== '' ? (
          <p className="filmony-text-panel mt-2 inline-block max-w-[min(100%,20rem)] text-sm text-(--tgui--hint_color,#94a3b8)">
            {subtitle}
          </p>
        ) : null}
        <p className="mt-1 font-mono text-xs text-(--tgui--hint_color,#94a3b8)">@{profile.profile_slug}</p>
      </div>
    </div>
  )
}
