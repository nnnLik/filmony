import { Button } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router-dom'

type EmptyStateAction = {
  label: string
  onClick?: () => void
  href?: string
}

type EmptyStateProps = {
  message: string
  action?: EmptyStateAction
  variant?: 'panel' | 'plain'
}

export function EmptyState({ message, action, variant = 'panel' }: EmptyStateProps) {
  if (variant === 'plain') {
    return (
      <div className="filmony-text-panel py-8 text-center">
        <p className="text-sm text-(--tgui--hint_color)">{message}</p>
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
      <p className="text-center text-[14px] leading-relaxed text-(--tgui--hint_color)">{message}</p>
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
