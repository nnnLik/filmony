import { Avatar, Button } from '@telegram-apps/telegram-ui'
import { useMemo } from 'react'
import { Link } from 'react-router'

import type { FilmCommunityCardItem } from '../../api/profileTypes'
import type { StreakBatchItem } from '../../api/streaksTypes'
import type { TasteQuizKnowledgeBatchItem } from '../../api/tasteQuizTypes'
import type { WatchingNowBatchItem } from '../../api/watchPartyTypes'
import { CommentBodyWithReactionTokens } from '../comments/CommentBodyWithReactionTokens'
import { TasteQuizCommentAuthorBadge } from '../tasteQuiz/TasteQuizCommentAuthorBadge'
import { RatingStreakAuthorBadge } from '../streaks/RatingStreakAuthorBadge'
import { WatchingNowAuthorBadge } from '../watchparty/WatchingNowAuthorBadge'
import {
  COMPANY_SHORT,
  MOOD_AFTER_SHORT,
  MOOD_BEFORE_SHORT,
  formatRating,
} from '../feed/feedCardUtils'
import { displayNameFromAuthorFields } from '../../lib/authorDisplayName'
import { profileInitials } from '../../lib/profileDisplay'
import { resolveApiMediaUrl } from '../../lib/resolveApiMediaUrl'
import type { CardCompany, CardMoodAfter, CardMoodBefore } from '../../api/profileTypes'

function companyLabel(c: string): string {
  return c in COMPANY_SHORT ? COMPANY_SHORT[c as CardCompany] : c
}

function moodBeforeLabel(m: string): string {
  return m in MOOD_BEFORE_SHORT ? MOOD_BEFORE_SHORT[m as CardMoodBefore] : m
}

function moodAfterLabel(m: string): string {
  return m in MOOD_AFTER_SHORT ? MOOD_AFTER_SHORT[m as CardMoodAfter] : m
}

type CommunityRatingsListProps = {
  items: FilmCommunityCardItem[]
  loading: boolean
  error: string | null
  nextCursor: string | null
  moreBusy: boolean
  viewerId: string | null
  tasteQuizKnowledgeByAuthor: Record<string, TasteQuizKnowledgeBatchItem>
  streakByUserId: Record<string, StreakBatchItem>
  watchingByUserId?: Record<string, WatchingNowBatchItem>
  followingUserIds?: ReadonlySet<string>
  onLoadMore: () => void
}

export function CommunityRatingsList({
  items,
  loading,
  error,
  nextCursor,
  moreBusy,
  viewerId,
  tasteQuizKnowledgeByAuthor,
  streakByUserId,
  watchingByUserId = {},
  followingUserIds,
  onLoadMore,
}: CommunityRatingsListProps) {
  const displayItems = useMemo(() => {
    if (followingUserIds == null) {
      return items
    }
    return items.filter(
      (row) =>
        followingUserIds.has(row.author.id) ||
        (viewerId != null && row.author.id === viewerId),
    )
  }, [items, followingUserIds, viewerId])

  return (
    <div className="px-3 py-3">
      {loading ? (
        <p className="text-center text-sm text-(--tgui--hint_color)">Загружаем оценки…</p>
      ) : null}
      {error != null ? (
        <p className="text-sm text-(--tgui--destructive_text_color)">{error}</p>
      ) : null}
      {!loading && error == null && items.length === 0 ? (
        <p className="text-[14px] leading-relaxed text-(--tgui--hint_color)">
          Пока никто не оценил эту тему в Filmony — станьте первым.
        </p>
      ) : null}
      {!loading && error == null && items.length > 0 && displayItems.length === 0 && followingUserIds != null ? (
        <p className="text-[14px] leading-relaxed text-(--tgui--hint_color)">
          Пока никто из ваших подписок не оценил эту тему.
        </p>
      ) : null}
      {!loading && error == null && displayItems.length > 0 ? (
        <ul className="flex flex-col gap-3">
          {displayItems.map((row) => {
            const name = displayNameFromAuthorFields(row.author)
            const photo = row.author.photo_url != null ? resolveApiMediaUrl(row.author.photo_url) : null
            const meta = `${formatRating(row.rating)} · ${companyLabel(row.company)} · ${moodBeforeLabel(row.mood_before)} → ${moodAfterLabel(row.mood_after)}`
            const isFriend = followingUserIds?.has(row.author.id) === true
            return (
              <li
                key={row.id}
                className="rounded-xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] p-3"
              >
                <div className="flex gap-3">
                  <Link
                    to={`/u/${encodeURIComponent(row.author.id)}`}
                    className="shrink-0 no-underline"
                    aria-label={`Профиль ${name}`}
                  >
                    <Avatar
                      size={40}
                      src={photo ?? undefined}
                      acronym={profileInitials(row.author)}
                    />
                  </Link>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                      <Link
                        to={`/u/${encodeURIComponent(row.author.id)}`}
                        className="truncate font-medium text-(--tgui--text_color) no-underline hover:opacity-90"
                      >
                        {name}
                      </Link>
                      {isFriend ? (
                        <span className="shrink-0 rounded-md border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_38%,transparent)] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_10%,transparent)] px-1.5 py-0.5 text-[10px] font-semibold text-(--tgui--text_color)">
                          Подписка
                        </span>
                      ) : null}
                      <TasteQuizCommentAuthorBadge
                        knowledgeByAuthor={tasteQuizKnowledgeByAuthor}
                        authorId={row.author.id}
                        viewerId={viewerId}
                      />
                      <RatingStreakAuthorBadge streakByUserId={streakByUserId} authorId={row.author.id} />
                      <WatchingNowAuthorBadge watchingByUserId={watchingByUserId} authorId={row.author.id} />
                      <Link
                        to={`/cards/${encodeURIComponent(String(row.id))}`}
                        className="shrink-0 text-xs font-semibold text-(--tgui--link_color) no-underline"
                      >
                        Карточка →
                      </Link>
                    </div>
                    <p className="mt-1 text-xs text-(--tgui--hint_color)">{meta}</p>
                    {row.watch_note.trim() !== '' ? (
                      <details className="mt-2 rounded-lg bg-[color-mix(in_srgb,var(--tgui--bg_color)_60%,transparent)] px-2 py-1.5">
                        <summary className="cursor-pointer text-xs font-medium text-(--tgui--link_color)">
                          Заметка к карточке
                        </summary>
                        <div className="mt-2 text-[13px] leading-snug text-(--tgui--text_color)">
                          <CommentBodyWithReactionTokens text={row.watch_note} />
                        </div>
                      </details>
                    ) : null}
                    {row.custom_tags.length > 0 ? (
                      <p className="mt-2 text-[11px] text-(--tgui--hint_color)">
                        {row.custom_tags.map((t) => `#${t}`).join(' ')}
                      </p>
                    ) : null}
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      ) : null}
      {nextCursor != null ? (
        <Button
          className="mt-4"
          mode="gray"
          stretched
          disabled={moreBusy}
          onClick={onLoadMore}
        >
          {moreBusy ? 'Загрузка…' : 'Показать ещё'}
        </Button>
      ) : null}
    </div>
  )
}
