import { Avatar, Button } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router-dom'

import type { TasteQuizKnowledgeItem } from '../../api/tasteQuizTypes'
import { displayNameFromProfile, profileInitials } from '../../lib/profileDisplay'
import { tasteQuizAccuracyColor } from '../../lib/tasteQuizAccuracyColor'

export type TasteQuizKnowledgeListProps = {
  items: TasteQuizKnowledgeItem[]
  emptyCopy: string
  loading?: boolean
  loadingMore?: boolean
  onLoadMore?: () => void
  hasMore?: boolean
}

export function TasteQuizKnowledgeList({
  items,
  emptyCopy,
  loading = false,
  loadingMore = false,
  onLoadMore,
  hasMore = false,
}: TasteQuizKnowledgeListProps) {
  if (loading && items.length === 0) {
    return <p className="filmony-text-panel py-8 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
  }

  if (!loading && items.length === 0) {
    return (
      <p className="filmony-text-panel py-8 text-center text-sm leading-relaxed text-(--tgui--hint_color)">
        {emptyCopy}
      </p>
    )
  }

  return (
    <div className="space-y-3">
      <ul className="divide-y divide-(--tgui--divider_color) overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--bg_color)">
        {items.map((item) => {
          const profile = {
            id: item.user_id,
            profile_slug: item.profile_slug,
            username: null,
            first_name: null,
            last_name: null,
            photo_url: item.avatar_url,
            display_name: item.display_name,
            bio: null,
            cards_count: 0,
            favorites_count: 0,
            watchlist_count: 0,
            friends_count: 0,
            followers_count: 0,
            following_count: 0,
          }
          const name = displayNameFromProfile(profile)
          const color = tasteQuizAccuracyColor(item.accuracy_pct)

          return (
            <li key={item.user_id}>
              <Link
                to={`/u/${encodeURIComponent(item.user_id)}`}
                className="flex items-center gap-3 px-3 py-3 no-underline transition hover:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)]"
              >
                <Avatar
                  src={item.avatar_url ?? undefined}
                  acronym={profileInitials(profile)}
                  size={40}
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-(--tgui--text_color)">{name}</p>
                  <p className="text-xs text-(--tgui--hint_color)">{item.attempts} попыток</p>
                </div>
                <div className="shrink-0 text-right">
                  <p className="text-base font-semibold tabular-nums" style={{ color }}>
                    {item.accuracy_pct}%
                  </p>
                  <p className="text-xs tabular-nums text-(--tgui--hint_color)">{item.points_sum} очк.</p>
                </div>
              </Link>
            </li>
          )
        })}
      </ul>
      {hasMore && onLoadMore != null ? (
        <Button mode="gray" stretched disabled={loadingMore} onClick={onLoadMore}>
          {loadingMore ? 'Загрузка…' : 'Показать ещё'}
        </Button>
      ) : null}
    </div>
  )
}
