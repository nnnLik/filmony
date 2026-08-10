import { Avatar } from '@telegram-apps/telegram-ui'
import { Crown } from 'lucide-react'

import type { WatchPartyMember } from '../../api/watchPartyTypes'

export type WatchPartyMemberStripProps = {
  members: WatchPartyMember[]
  onTap?: () => void
}

export function WatchPartyMemberStrip({ members, onTap }: WatchPartyMemberStripProps) {
  const visible = members.filter((m) => m.status === 'active' || m.status === 'away')
  if (visible.length === 0) {
    return null
  }

  return (
    <button
      type="button"
      onClick={onTap}
      className="flex w-full items-center gap-2 overflow-x-auto px-3 py-1.5 text-left"
      aria-label={`Участники: ${visible.length}`}
    >
      {visible.map((member) => (
        <div key={member.user_id} className="relative shrink-0">
          <Avatar size={32} src={member.photo_url ?? undefined} />
          {member.role === 'host' ? (
            <Crown className="absolute -right-0.5 -top-0.5 size-3 text-amber-300" strokeWidth={2.5} />
          ) : null}
        </div>
      ))}
      <span className="shrink-0 text-xs text-(--tgui--hint_color)">
        {visible.length}
        {' '}
        {visible.length === 1 ? 'зритель' : visible.length < 5 ? 'зрителя' : 'зрителей'}
      </span>
    </button>
  )
}
