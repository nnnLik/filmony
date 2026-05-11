import { Avatar } from '@telegram-apps/telegram-ui'
import { useMemo } from 'react'
import { Link } from 'react-router-dom'

import { resolveApiUrl } from '../../api/client'
import type { FeedPostInFeed } from '../../api/feedInFeedTypes'
import { MentionProfileLookupProvider } from '../../context/MentionProfileLookupProvider'
import { authorLikeToMentionRow } from '../../lib/mentionProfileLookupUtils'
import { CommentBodyWithReactionTokens } from '../comments/CommentBodyWithReactionTokens'
import { displayNameFromAuthorFields } from '../../lib/authorDisplayName'
import { formatCommentTime, formatRating } from './feedCardUtils'
import { feedPostSourceBadge } from './feedPostSourceBadge'

export type FeedPostCardProps = {
  post: FeedPostInFeed
  viewerUserId?: string | null
}

function feedPostImageSrc(url: string): string {
  const u = url.trim()
  if (u.startsWith('http://') || u.startsWith('https://')) return u
  return resolveApiUrl(u.startsWith('/') ? u : `/${u}`)
}

export function FeedPostCard({ post, viewerUserId = null }: FeedPostCardProps) {
  const {
    id,
    user_id,
    author,
    body,
    created_at,
    referenced_card,
    image_url,
    source_comment_id,
  } = post

  const name = useMemo(() => displayNameFromAuthorFields(author), [author])
  const mentionProfileRows = useMemo(() => [authorLikeToMentionRow(author)], [author])
  const profileHref = `/u/${encodeURIComponent(user_id)}`
  const sourceBadgeText = useMemo(
    () => feedPostSourceBadge(post, viewerUserId ?? null),
    [post, viewerUserId],
  )
  const isOwn =
    viewerUserId != null && viewerUserId !== '' && user_id === viewerUserId

  return (
    <MentionProfileLookupProvider value={mentionProfileRows}>
    <article
      data-testid={`feed-post-${id}`}
      data-feed-post-id={id}
      className={`feed-post-card flex max-w-full flex-col gap-2 overflow-hidden rounded-2xl p-2.5 shadow-[0_10px_40px_-14px_rgba(0,0,0,0.45)] ${
        isOwn
          ? 'border-2 border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_42%,transparent)] bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)]'
          : 'border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_96%,transparent)]'
      }`}
    >
      <div className="mb-0.5 flex flex-wrap items-center gap-2 px-0.5">
        <span
          className="shrink-0 rounded-md border border-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_42%,transparent)] bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_12%,transparent)] px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-(--tgui--text_color)"
          title="Текстовый пост в ленте"
        >
          {sourceBadgeText}
        </span>
        {source_comment_id != null ? (
          <span
            className="shrink-0 rounded-md border border-(--tgui--divider_color) bg-(--tgui--section_bg_color) px-1.5 py-0.5 text-[10px] font-medium text-(--tgui--hint_color)"
            title="Текст взят из вашего комментария к карточке"
          >
            Из комментария
          </span>
        ) : null}
      </div>

      <div className="flex min-w-0 flex-col gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <Link
            to={profileHref}
            className="relative z-10 flex shrink-0 rounded-full p-0.5 no-underline ring-1 ring-transparent transition-[box-shadow,ring-color] hover:ring-(--tgui--link_color) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--tgui--link_color)"
            title={name}
            aria-label={`Профиль: ${name}`}
          >
            <Avatar
              size={22}
              src={author.photo_url ?? undefined}
              acronym={(name.slice(0, 1) || '?').toUpperCase()}
            />
          </Link>
          <div className="min-w-0 flex-1">
            <div className="flex min-w-0 flex-wrap items-baseline gap-x-2 gap-y-0.5">
              <Link
                to={profileHref}
                className="truncate text-sm font-medium text-(--tgui--link_color) no-underline"
              >
                {name}
              </Link>
              <span className="shrink-0 text-[11px] text-(--tgui--hint_color)">
                {formatCommentTime(created_at)}
              </span>
            </div>
          </div>
        </div>

        {body.trim() !== '' ? (
          <p className="line-clamp-6 text-[13px] leading-relaxed text-(--tgui--text_color)">
            <CommentBodyWithReactionTokens text={body} className="text-[13px] leading-relaxed" />
          </p>
        ) : null}

        {referenced_card != null ? (
          <Link
            to={`/cards/${referenced_card.movie_card_id}`}
            state={{ fromFeed: true }}
            className="flex min-w-0 gap-2.5 rounded-xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] p-2 no-underline transition-[border-color,box-shadow] active:opacity-95 hover:border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_28%,var(--tgui--divider_color))]"
          >
            <div className="relative h-14 w-10 shrink-0 overflow-hidden rounded-lg bg-(--tgui--divider_color) ring-1 ring-(--tgui--divider_color)">
              {referenced_card.film_poster_url ? (
                <img src={referenced_card.film_poster_url} alt="" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center text-[9px] text-(--tgui--hint_color)">
                  н/д
                </div>
              )}
            </div>
            <div className="min-w-0 flex-1 py-0.5">
              <div className="flex min-w-0 items-start justify-between gap-2">
                <p className="line-clamp-2 min-w-0 flex-1 text-[13px] font-semibold leading-snug text-(--tgui--text_color)">
                  {referenced_card.film_title}
                  {referenced_card.film_year != null ? (
                    <span className="font-normal text-(--tgui--hint_color)"> · {referenced_card.film_year}</span>
                  ) : null}
                </p>
                <span className="shrink-0 rounded-md bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_18%,transparent)] px-1.5 py-0.5 text-[12px] font-bold tabular-nums text-(--tgui--text_color)">
                  {formatRating(referenced_card.rating)}
                </span>
              </div>
            </div>
          </Link>
        ) : null}

        {image_url != null && image_url.trim() !== '' ? (
          <div className="mt-1 overflow-hidden rounded-xl bg-(--tgui--divider_color) ring-1 ring-(--tgui--divider_color)">
            <img
              src={feedPostImageSrc(image_url)}
              alt=""
              className="max-h-[min(70vw,18rem)] w-full object-cover object-center"
              loading="lazy"
            />
          </div>
        ) : null}
      </div>
    </article>
    </MentionProfileLookupProvider>
  )
}
