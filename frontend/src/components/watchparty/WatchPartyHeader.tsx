import { IconButton } from '@telegram-apps/telegram-ui'
import { ArrowLeft, MessageCircle, UserPlus, Users } from 'lucide-react'

export type WatchPartyHeaderProps = {
  title: string
  memberCount: number
  onBack: () => void
  onMemberCountTap: () => void
  onChat: () => void
  onInvite?: () => void
}

export function WatchPartyHeader({
  title,
  memberCount,
  onBack,
  onMemberCountTap,
  onChat,
  onInvite,
}: WatchPartyHeaderProps) {
  return (
    <header className="flex items-center gap-2 border-b border-white/10 px-3 py-2">
      <IconButton mode="gray" size="s" onClick={onBack} aria-label="Назад">
        <ArrowLeft className="block size-5" strokeWidth={2} />
      </IconButton>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold">{title}</p>
        <button
          type="button"
          onClick={onMemberCountTap}
          className="flex items-center gap-1 text-xs text-(--tgui--hint_color)"
        >
          <Users className="size-3.5" />
          {memberCount}
        </button>
      </div>
      {onInvite != null ? (
        <IconButton mode="gray" size="s" onClick={onInvite} aria-label="Пригласить друзей">
          <UserPlus className="block size-5" strokeWidth={2} />
        </IconButton>
      ) : null}
      <IconButton mode="gray" size="s" onClick={onChat} aria-label="Чат">
        <MessageCircle className="block size-5" strokeWidth={2} />
      </IconButton>
    </header>
  )
}
