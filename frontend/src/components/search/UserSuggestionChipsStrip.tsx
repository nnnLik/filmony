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
  hint?: string
  users: SearchUserItem[]
}

export function UserSuggestionChipsStrip({ title, hint, users }: UserSuggestionChipsStripProps) {
  if (users.length === 0) return null
  return (
    <section className="rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,.04)]">
      <div className="mb-2.5 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="text-[13px] font-semibold leading-tight tracking-tight text-(--tgui--text_color)">
            {title}
          </h3>
          {hint ? <p className="mt-0.5 text-[11px] leading-snug text-(--tgui--hint_color)">{hint}</p> : null}
        </div>
        <span className="shrink-0 rounded-full bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_12%,transparent)] px-2 py-0.5 text-[11px] font-medium tabular-nums text-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_95%,var(--tgui--text_color))]">
          {users.length}
        </span>
      </div>
      <div
        className="-mx-1 flex snap-x snap-mandatory gap-2.5 overflow-x-auto scroll-px-2 px-1 pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        role="list"
      >
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
              role="listitem"
              className="group flex w-[4.75rem] shrink-0 snap-start flex-col items-center gap-1.5 rounded-xl px-1 py-1 no-underline text-(--tgui--text_color) transition-[background,transform] duration-200 ease-out active:scale-[0.98] hover:bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_08%,transparent)]"
            >
              <div className="relative flex size-[52px] shrink-0 items-center justify-center rounded-full bg-(--tgui--bg_color) shadow-[0_0_0_1px_color-mix(in_srgb,var(--tgui--divider_color)_80%,transparent)] transition-shadow duration-200 group-hover:shadow-[0_0_0_2px_color-mix(in_srgb,var(--filmony-mint,#5eead4)_35%,transparent)]">
                <Avatar size={48} src={u.photo_url ?? undefined} acronym={initials} />
              </div>
              <span className="line-clamp-2 w-full text-center text-[11px] font-medium leading-tight">{label}</span>
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
