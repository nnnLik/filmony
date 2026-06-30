import { Avatar } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router-dom'

import type { MovieCardCommentAuthor } from '../../api/profileTypes'
import { displayNameFromProfile, profileInitials } from '../../lib/profileDisplay'

type PlannedWatchPartnersListProps = {
  partners: MovieCardCommentAuthor[]
  className?: string
}

export function PlannedWatchPartnersList({ partners, className = '' }: PlannedWatchPartnersListProps) {
  if (partners.length === 0) {
    return null
  }

  return (
    <div className={className}>
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-(--tgui--hint_color)">
        Смотреть вместе
      </p>
      <ul className="mt-2.5 list-none space-y-1.5 p-0">
        {partners.map((partner) => {
          const name = displayNameFromProfile(partner)
          return (
            <li key={partner.id}>
              <Link
                to={`/u/${encodeURIComponent(partner.id)}`}
                className="flex items-center gap-3 rounded-xl px-1 py-1.5 no-underline outline-none transition-colors duration-200 motion-safe:hover:bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_06%,transparent)] ring-(--tgui--link_color) focus-visible:ring-2"
              >
                <Avatar
                  src={partner.photo_url ?? undefined}
                  acronym={profileInitials(partner)}
                  size={40}
                />
                <span className="min-w-0 flex-1 truncate text-sm font-medium text-(--tgui--text_color)">
                  {name}
                </span>
              </Link>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
