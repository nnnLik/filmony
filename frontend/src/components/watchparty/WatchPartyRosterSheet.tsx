import { Avatar, IconButton } from '@telegram-apps/telegram-ui'
import { Crown, X } from 'lucide-react'
import { createPortal } from 'react-dom'

import type { WatchPartyMember } from '../../api/watchPartyTypes'
import type { WatchingNowBatchItem } from '../../api/watchPartyTypes'
import { WatchingNowAuthorBadge } from './WatchingNowAuthorBadge'

export type WatchPartyRosterSheetProps = {
  open: boolean
  members: WatchPartyMember[]
  watchingByUserId?: Record<string, WatchingNowBatchItem>
  onClose: () => void
}

export function WatchPartyRosterSheet({
  open,
  members,
  watchingByUserId = {},
  onClose,
}: WatchPartyRosterSheetProps) {
  if (!open) {
    return null
  }

  return createPortal(
    <div className="filmony-theme fixed inset-0 z-50 flex flex-col justify-end text-(--tgui--text_color) pointer-events-auto">
      <button
        type="button"
        className="absolute inset-0 bg-[color-mix(in_srgb,var(--filmony-ink,#06090d)_72%,transparent)]"
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div
        className="relative z-10 mx-auto w-full max-w-md rounded-t-[22px] border border-(--tgui--divider_color) bg-(--tgui--tertiary_bg_color) p-4 shadow-[0_-16px_48px_rgba(0,0,0,0.5)]"
        role="dialog"
        aria-modal="true"
      >
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">Участники</h2>
          <IconButton mode="gray" size="s" onClick={onClose} aria-label="Закрыть">
            <X className="block size-5" />
          </IconButton>
        </div>
        <ul className="max-h-[50dvh] space-y-2 overflow-y-auto">
          {members.map((member) => (
            <li
              key={member.user_id}
              className="flex items-center gap-3 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-3 py-2"
            >
              <div className="relative shrink-0">
                <Avatar size={40} src={member.photo_url ?? undefined} />
                {member.role === 'host' ? (
                  <Crown className="absolute -right-1 -top-1 size-3.5 text-amber-300" />
                ) : null}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-0.5">
                  <span className="truncate text-sm font-medium">{member.display_name}</span>
                  <WatchingNowAuthorBadge
                    watchingByUserId={watchingByUserId}
                    authorId={member.user_id}
                  />
                </div>
                <p className="text-xs text-(--tgui--hint_color)">
                  {member.status === 'away'
                    ? 'Отошёл'
                    : member.status === 'left'
                      ? 'Вышел'
                      : member.role === 'host'
                        ? 'Ведущий'
                        : 'Гость'}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>,
    document.body,
  )
}
