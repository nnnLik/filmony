import { Button } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router'

import type { MicroFunPoolKey } from '../../lib/microFun'
import { useMicroFunLine } from '../../lib/microFun'

type EmptyStateAction = {
  label: string
  onClick?: () => void
  href?: string
}

type EmptyStateProps = {
  message: string
  action?: EmptyStateAction
  variant?: 'panel' | 'plain'
  playfulKey?: MicroFunPoolKey
  playfulSeedUserId?: string | number | null
  /** Prepended to playful line (e.g. greeting + comma). */
  playfulMessagePrefix?: string
}

export function EmptyState({
  message,
  action,
  variant = 'panel',
  playfulKey,
  playfulSeedUserId,
  playfulMessagePrefix,
}: EmptyStateProps) {
  const playfulLine = useMicroFunLine(
    playfulKey ?? 'feed_empty',
    message,
    playfulKey != null ? (playfulSeedUserId ?? null) : null,
  )
  const displayMessage =
    playfulKey != null ? `${playfulMessagePrefix ?? ''}${playfulLine}` : message

  if (variant === 'plain') {
    return (
      <div className="filmony-text-panel py-8 text-center">
        <p className="text-sm text-(--tgui--hint_color)">{displayMessage}</p>
        {action != null ? (
          <div className="mt-4">
            {action.href != null ? (
              <Link to={action.href} className="no-underline">
                <Button stretched onClick={action.onClick}>
                  {action.label}
                </Button>
              </Link>
            ) : (
              <Button stretched onClick={action.onClick}>
                {action.label}
              </Button>
            )}
          </div>
        ) : null}
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-4 rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] px-4 py-10">
      <p className="text-center text-[14px] leading-relaxed text-(--tgui--hint_color)">{displayMessage}</p>
      {action != null ? (
        action.href != null ? (
          <Link to={action.href} className="w-full no-underline">
            <Button stretched onClick={action.onClick}>
              {action.label}
            </Button>
          </Link>
        ) : (
          <Button stretched onClick={action.onClick}>
            {action.label}
          </Button>
        )
      ) : null}
    </div>
  )
}
