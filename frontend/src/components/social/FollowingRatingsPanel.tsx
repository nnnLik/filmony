import { Avatar } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router'

import {
  followingRowDisplayName,
  followingRowInitials,
  followingRowShowsPlannedLabel,
  type FollowingRatingRow,
} from '../../lib/followingRatingsDisplay'

function formatRating(value: number): string {
  if (!Number.isFinite(value)) return '0'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function ratingPalette(value: number): { text: string } {
  if (value >= 8) return { text: 'var(--filmony-mint, #5eead4)' }
  if (value >= 5) return { text: 'var(--filmony-amber, #e8b86d)' }
  return { text: 'var(--tgui--destructive_text_color, #ef7d9b)' }
}

function FollowingRatingsSkeleton() {
  return (
    <ul className="mt-3 list-none space-y-1.5 p-0">
      {[0, 1, 2].map((i) => (
        <li
          key={i}
          className="flex animate-pulse items-center gap-3 rounded-xl px-1 py-1.5"
          aria-hidden
        >
          <div className="size-10 shrink-0 rounded-full bg-[color-mix(in_srgb,var(--tgui--hint_color)_14%,transparent)]" />
          <div className="h-4 min-w-0 flex-1 rounded bg-[color-mix(in_srgb,var(--tgui--hint_color)_12%,transparent)]" />
          <div className="h-5 w-8 shrink-0 rounded bg-[color-mix(in_srgb,var(--tgui--hint_color)_10%,transparent)]" />
        </li>
      ))}
    </ul>
  )
}

export type FollowingRatingsPanelProps = {
  rows: FollowingRatingRow[] | null
  /** Optional link to full community ratings (e.g. catalog detail). */
  communityLink?: { to: string; label?: string } | null
  className?: string
}

export function FollowingRatingsPanel({ rows, communityLink = null, className = '' }: FollowingRatingsPanelProps) {
  return (
    <section
      className={`rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:p-4 ${className}`.trim()}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">
            Друзья оценили
          </p>
          <p className="mt-1 text-[11px] leading-snug text-(--tgui--secondary_hint_color)">Сравнить с подписками.</p>
        </div>
        {communityLink != null ? (
          <Link
            to={communityLink.to}
            className="shrink-0 text-xs font-semibold text-(--tgui--link_color) no-underline"
          >
            {communityLink.label ?? 'Все оценки →'}
          </Link>
        ) : null}
      </div>
      {rows == null ? (
        <FollowingRatingsSkeleton />
      ) : rows.length === 0 ? (
        <div className="mt-3 space-y-2">
          <p className="text-sm text-(--tgui--hint_color)">
            Пока никто из подписок не оценил эту тему.
          </p>
          <Link to="/profile/subscriptions" className="text-sm font-semibold text-(--tgui--link_color) no-underline">
            Найти друзей в подписках →
          </Link>
        </div>
      ) : (
        <ul className="mt-3 list-none space-y-1.5 p-0">
          {rows.map((row) => {
            const showsPlanned = followingRowShowsPlannedLabel(row)
            const rp = showsPlanned ? null : ratingPalette(row.rating ?? 0)
            return (
              <li key={row.movie_card_id}>
                <Link
                  to={`/cards/${row.movie_card_id}`}
                  className="flex items-center gap-3 rounded-xl px-1 py-1.5 no-underline outline-none transition-colors duration-200 motion-safe:hover:bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_06%,transparent)] ring-(--tgui--link_color) focus-visible:ring-2"
                >
                  <Avatar
                    src={row.photo_url ?? undefined}
                    acronym={followingRowInitials(row)}
                    size={40}
                  />
                  <span className="min-w-0 flex-1 truncate text-sm font-medium text-(--tgui--text_color)">
                    {followingRowDisplayName(row)}
                  </span>
                  {showsPlanned ? (
                    <span className="shrink-0 text-sm font-medium text-(--tgui--hint_color)">
                      {row.is_viewer ? 'У вас в планах' : 'В «Позже»'}
                    </span>
                  ) : (
                    <span
                      className="shrink-0 text-lg font-semibold tabular-nums"
                      style={{ color: rp?.text }}
                    >
                      {formatRating(row.rating ?? 0)}
                    </span>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
