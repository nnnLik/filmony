import { Avatar, Button, Title } from '@telegram-apps/telegram-ui'

import type { PublicProfile, SubscriptionListItem } from '../../api/profileTypes'
import { copyTextToClipboard } from '../../lib/copyTextToClipboard'
import { displayNameFromProfile, profileInitials } from '../../lib/profileDisplay'
import { safeHapticSuccess } from '../../lib/safeHaptic'

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

export type ShareFollowersPickerPreview = {
  posterUrl: string | null
  title: string
  yearLabel: string
}

export type ShareFollowersPickerProps = {
  preview: ShareFollowersPickerPreview
  hint?: string
  followers: SubscriptionListItem[]
  loading: boolean
  selected: Set<string>
  onToggle: (userId: string) => void
  deepLinkToCopy?: string | null
}

export function ShareFollowersPicker({
  preview,
  hint = 'Выберите подписчиков — им уйдёт сообщение в Telegram с постером, оценкой и тегами карточки.',
  followers,
  loading,
  selected,
  onToggle,
  deepLinkToCopy = null,
}: ShareFollowersPickerProps) {
  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
        <div className="aspect-video w-full">
          {preview.posterUrl ? (
            <img src={preview.posterUrl} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-(--tgui--hint_color)">Нет постера</div>
          )}
        </div>
        <div className="px-4 py-3">
          <Title level="3" weight="2" className="line-clamp-2">
            {preview.title}
          </Title>
          <p className="mt-1 text-sm text-(--tgui--hint_color)">{preview.yearLabel}</p>
        </div>
      </div>

      {deepLinkToCopy != null && deepLinkToCopy !== '' ? (
        <Button
          mode="gray"
          stretched
          type="button"
          onClick={() => {
            void (async () => {
              const ok = await copyTextToClipboard(deepLinkToCopy)
              if (ok) {
                safeHapticSuccess()
              }
            })()
          }}
        >
          Скопировать ссылку
        </Button>
      ) : null}

      <p className="filmony-text-panel text-sm leading-relaxed text-(--tgui--hint_color)">{hint}</p>

      {loading ? (
        <p className="filmony-text-panel py-6 text-center text-sm text-(--tgui--hint_color)">Загрузка подписчиков…</p>
      ) : null}

      {!loading && followers.length === 0 ? (
        <p className="filmony-text-panel text-center text-sm text-(--tgui--hint_color)">
          Пока нет подписчиков. Когда кто-то подпишется на вас, вы сможете делиться здесь.
        </p>
      ) : null}

      {!loading && followers.length > 0 ? (
        <ul className="flex flex-col gap-2">
          {followers.map((row) => {
            const pub = toPublicFromSubscription(row)
            const name = displayNameFromProfile(pub)
            const checked = selected.has(row.id)
            return (
              <li key={row.id}>
                <button
                  type="button"
                  onClick={() => onToggle(row.id)}
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
