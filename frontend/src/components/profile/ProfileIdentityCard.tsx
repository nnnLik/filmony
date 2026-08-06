import { Avatar } from '@telegram-apps/telegram-ui'
import { useState, type ReactNode } from 'react'

import type { PublicProfile } from '../../api/profileTypes'
import type { StreakBatchItem } from '../../api/streaksTypes'
import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import { displayNameFromProfile, profileInitials } from '../../lib/profileDisplay'
import { RatingStreakAuthorBadge } from '../streaks/RatingStreakAuthorBadge'
import { TasteQuizCommentAuthorBadge } from '../tasteQuiz/TasteQuizCommentAuthorBadge'

export type ProfileIdentityCardProps = {
  profile: PublicProfile
  viewerId?: string | null
  knowledgeByOwnerId?: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId?: Record<string, StreakBatchItem>
  /** Compact control aligned with the name row (follow button, etc.). */
  headerAction?: ReactNode
  /** Metric chips row. */
  metrics?: ReactNode
  /** Secondary actions rendered as one compact row under the metrics. */
  actions?: ReactNode
  className?: string
}

export function ProfileIdentityCard({
  profile,
  viewerId = null,
  knowledgeByOwnerId = {},
  streakByUserId = {},
  headerAction,
  metrics,
  actions,
  className,
}: ProfileIdentityCardProps) {
  const [bioExpanded, setBioExpanded] = useState(false)
  const name = displayNameFromProfile(profile)
  const bio = profile.bio?.trim() ?? ''
  const bioIsLong = bio.length > 90

  return (
    <section className={`flex flex-col gap-3 ${className ?? ''}`}>
      <div className="flex items-center gap-3">
        <div className="shrink-0">
          <Avatar
            src={profile.photo_url ?? undefined}
            acronym={profileInitials(profile)}
            size={64}
          />
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-1.5">
          <div className="flex min-w-0 items-center gap-1.5">
            <h2 className="min-w-0 truncate text-[17px] font-semibold leading-tight tracking-tight text-(--tgui--text_color)">
              {name}
            </h2>
            <TasteQuizCommentAuthorBadge
              knowledgeByAuthor={knowledgeByOwnerId}
              authorId={profile.id}
              viewerId={viewerId}
            />
            <RatingStreakAuthorBadge streakByUserId={streakByUserId} authorId={profile.id} />
          </div>
          <p className="truncate font-mono text-[11px] leading-none text-(--tgui--hint_color)">
            @{profile.profile_slug}
          </p>
        </div>
        {headerAction != null ? <div className="shrink-0">{headerAction}</div> : null}
      </div>

      {bio !== '' ? (
        <div>
          <p
            className={`text-[13px] leading-relaxed text-(--tgui--hint_color) ${
              bioExpanded ? '' : 'line-clamp-2'
            }`}
          >
            {bio}
          </p>
          {bioIsLong ? (
            <button
              type="button"
              className="mt-1 text-[12px] font-medium text-(--tgui--link_color)"
              onClick={() => setBioExpanded((prev) => !prev)}
            >
              {bioExpanded ? 'Свернуть' : 'Ещё'}
            </button>
          ) : null}
        </div>
      ) : null}

      {metrics}

      {actions != null ? <div className="flex items-center gap-2">{actions}</div> : null}
    </section>
  )
}
