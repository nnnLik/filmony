import { Avatar } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router'
import type { ReactNode } from 'react'

import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import type { StreakBatchItem } from '../../api/streaksTypes'
import type { WatchingNowBatchItem } from '../../api/watchPartyTypes'
import { commentAuthorLabel, formatCommentTime } from '../../lib/commentDisplay'
import type { ThreadCommentAuthor } from '../../lib/commentThreadTypes'
import { TasteQuizCommentAuthorBadge } from '../tasteQuiz/TasteQuizCommentAuthorBadge'
import { RatingStreakAuthorBadge } from '../streaks/RatingStreakAuthorBadge'
import { WatchingNowAuthorBadge } from '../watchparty/WatchingNowAuthorBadge'

export type CommentAuthorRowProps = {
  author: ThreadCommentAuthor
  createdAt: string
  viewerId?: string | null
  knowledgeByAuthor?: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId?: Record<string, StreakBatchItem>
  watchingByUserId?: Record<string, WatchingNowBatchItem>
  avatarSize?: 24 | 28
  nameAsLink?: boolean
  trailing?: ReactNode
  onMouseDown?: React.MouseEventHandler
}

export function CommentAuthorRow({
  author,
  createdAt,
  viewerId = null,
  knowledgeByAuthor,
  streakByUserId,
  watchingByUserId,
  avatarSize = 28,
  nameAsLink = true,
  trailing,
  onMouseDown,
}: CommentAuthorRowProps) {
  const label = commentAuthorLabel(author)
  const authorHref = `/u/${encodeURIComponent(author.id)}`
  const nameClass =
    nameAsLink === true
      ? 'text-sm font-medium text-(--tgui--link_color) no-underline'
      : 'text-sm font-medium text-(--tgui--text_color)'

  return (
    <div className="flex items-start gap-2">
      <Link
        to={authorHref}
        className="shrink-0 no-underline"
        aria-label={`Профиль: ${label}`}
        onClick={(e) => e.stopPropagation()}
        onMouseDown={onMouseDown}
      >
        <Avatar
          src={author.photo_url ?? undefined}
          acronym={label.slice(0, 2).toUpperCase()}
          size={avatarSize}
        />
      </Link>
      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 items-start justify-between gap-2">
          <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-0.5">
            {nameAsLink ? (
              <Link
                to={authorHref}
                className={nameClass}
                onClick={(e) => e.stopPropagation()}
                onMouseDown={onMouseDown}
              >
                {label}
              </Link>
            ) : (
              <span className={nameClass}>{label}</span>
            )}
            {knowledgeByAuthor != null ? (
              <TasteQuizCommentAuthorBadge
                knowledgeByAuthor={knowledgeByAuthor}
                authorId={author.id}
                viewerId={viewerId}
              />
            ) : null}
            {streakByUserId != null ? (
              <RatingStreakAuthorBadge streakByUserId={streakByUserId} authorId={author.id} />
            ) : null}
            {watchingByUserId != null ? (
              <WatchingNowAuthorBadge watchingByUserId={watchingByUserId} authorId={author.id} />
            ) : null}
            <span className="text-xs text-(--tgui--hint_color)">{formatCommentTime(createdAt)}</span>
          </div>
          {trailing}
        </div>
      </div>
    </div>
  )
}
