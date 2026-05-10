import { Avatar } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router-dom'

import type { SearchUserItem } from '../../api/searchApi'
import { profileInitials } from '../../lib/profileDisplay'

function userListLabel(u: SearchUserItem): string {
  if (u.display_name?.trim()) {
    return u.display_name.trim()
  }
  if (u.username?.trim()) {
    return `@${u.username.trim()}`
  }
  return `@${u.profile_slug}`
}

function userSummaryLine(u: SearchUserItem): string {
  const n = u.movie_cards_count ?? 0
  const parts: string[] = []
  if (n === 0) {
    parts.push('нет карт.')
  } else if (n === 1) {
    parts.push('1 карт.')
  } else {
    parts.push(`${n} карт.`)
  }
  const avg = u.average_rating
  if (avg != null && n > 0) {
    parts.push(`⌀ ${avg.toFixed(1)}`)
  }
  return parts.join(' · ')
}

export type UserSuggestionChipsStripProps = {
  title: string
  users: SearchUserItem[]
}

export function UserSuggestionChipsStrip({ title, users }: UserSuggestionChipsStripProps) {
  if (users.length === 0) return null
  return (
    <section className="border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_55%,transparent)] px-4 py-2.5">
      <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-(--tgui--hint_color)">{title}</p>
      <div className="flex gap-3 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {users.map((u) => {
          const label = userListLabel(u)
          const initials = profileInitials({
            display_name: u.display_name,
            first_name: null,
            username: u.username,
          })
          return (
            <Link
              key={u.id}
              to={`/u/${encodeURIComponent(u.id)}`}
              className="flex w-19 shrink-0 flex-col items-center gap-1 no-underline text-(--tgui--text_color)"
            >
              <div className="flex size-13 shrink-0 items-center justify-center overflow-hidden rounded-full border border-(--tgui--divider_color) bg-(--tgui--bg_color)">
                <Avatar size={48} src={u.photo_url ?? undefined} acronym={initials} />
              </div>
              <span className="line-clamp-2 w-full text-center text-[11px] leading-tight">{label}</span>
              <span className="line-clamp-2 w-full text-center text-[10px] leading-tight text-(--tgui--hint_color)">
                {userSummaryLine(u)}
              </span>
            </Link>
          )
        })}
      </div>
    </section>
  )
}
