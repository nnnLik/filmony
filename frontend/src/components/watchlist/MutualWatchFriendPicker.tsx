import { Avatar } from '@telegram-apps/telegram-ui'

import type { PublicProfile, SubscriptionListItem } from '../../api/profileTypes'
import { displayNameFromProfile, profileInitials } from '../../lib/profileDisplay'

function toPublicFromSubscription(row: SubscriptionListItem): PublicProfile {
  return {
    id: row.id,
    profile_slug: row.profile_slug,
    username: row.username,
    first_name: row.first_name,
    last_name: row.last_name,
    photo_url: row.photo_url,
    display_name: row.display_name,
    bio: null,
    cards_count: 0,
    favorites_count: 0,
    watchlist_count: 0,
    friends_count: 0,
    followers_count: 0,
    following_count: 0,
  }
}

export type MutualWatchFriendPickerProps = {
  friends: SubscriptionListItem[]
  loading: boolean
  selectedUserId: string | null
  onSelect: (userId: string | null) => void
}

export function MutualWatchFriendPicker({
  friends,
  loading,
  selectedUserId,
  onSelect,
}: MutualWatchFriendPickerProps) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-(--tgui--text_color)">Смотреть вместе (необязательно)</p>
      <p className="text-xs text-(--tgui--hint_color)">
        Только взаимные подписки — друг получит отдельную запись в «Позже» и уведомление в Telegram.
      </p>

      {loading ? (
        <p className="py-4 text-center text-sm text-(--tgui--hint_color)">Загрузка друзей…</p>
      ) : null}

      {!loading && friends.length === 0 ? (
        <p className="text-sm text-(--tgui--hint_color)">
          Пока нет взаимных подписок — можно добавить в список только для себя.
        </p>
      ) : null}

      {!loading && friends.length > 0 ? (
        <ul className="flex flex-col gap-2">
          <li>
            <button
              type="button"
              onClick={() => onSelect(null)}
              className={`flex w-full items-center gap-3 rounded-2xl border px-3 py-2.5 text-left transition ${
                selectedUserId == null
                  ? 'border-(--tgui--link_color) bg-[color-mix(in_srgb,var(--tgui--link_color)_12%,var(--tgui--secondary_bg_color))]'
                  : 'border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)'
              }`}
            >
              <span className="flex size-5 shrink-0 items-center justify-center rounded border border-(--tgui--divider_color) bg-(--tgui--bg_color)">
                {selectedUserId == null ? (
                  <span className="text-xs text-(--tgui--link_color)">✓</span>
                ) : null}
              </span>
              <span className="text-sm font-medium text-(--tgui--text_color)">Только я</span>
            </button>
          </li>
          {friends.map((row) => {
            const pub = toPublicFromSubscription(row)
            const name = displayNameFromProfile(pub)
            const checked = selectedUserId === row.id
            return (
              <li key={row.id}>
                <button
                  type="button"
                  onClick={() => onSelect(checked ? null : row.id)}
                  className={`flex w-full items-center gap-3 rounded-2xl border px-3 py-2.5 text-left transition ${
                    checked
                      ? 'border-(--tgui--link_color) bg-[color-mix(in_srgb,var(--tgui--link_color)_12%,var(--tgui--secondary_bg_color))]'
                      : 'border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)'
                  }`}
                >
                  <span className="flex size-5 shrink-0 items-center justify-center rounded border border-(--tgui--divider_color) bg-(--tgui--bg_color)">
                    {checked ? <span className="text-xs text-(--tgui--link_color)">✓</span> : null}
                  </span>
                  <Avatar src={row.photo_url ?? undefined} acronym={profileInitials(pub)} size={40} />
                  <span className="min-w-0 flex-1 truncate text-sm font-medium">{name}</span>
                </button>
              </li>
            )
          })}
        </ul>
      ) : null}
    </div>
  )
}
