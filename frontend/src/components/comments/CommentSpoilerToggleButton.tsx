import { IconButton } from '@telegram-apps/telegram-ui'
import { EyeOff } from 'lucide-react'
import type { MouseEvent } from 'react'

export type CommentSpoilerToggleButtonProps = {
  onToggleSpoiler: () => void
  disabled?: boolean
  allowInsert?: boolean
}

export function CommentSpoilerToggleButton({
  onToggleSpoiler,
  disabled = false,
  allowInsert = true,
}: CommentSpoilerToggleButtonProps) {
  const blocked = disabled || !allowInsert

  return (
    <IconButton
      type="button"
      size="s"
      mode="gray"
      disabled={blocked}
      onClick={(e: MouseEvent<HTMLButtonElement>) => {
        e.stopPropagation()
        if (blocked) return
        onToggleSpoiler()
      }}
      aria-label="Пометить выделенный текст как спойлер"
      title="Спойлер"
      className="relative z-0 box-border! flex! h-8! w-8! min-h-8! min-w-8! shrink-0 items-center! justify-center! rounded-full p-0! leading-none! text-(--tgui--hint_color)"
    >
      <EyeOff className="relative z-1 block size-[18px] shrink-0" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" aria-hidden />
    </IconButton>
  )
}
