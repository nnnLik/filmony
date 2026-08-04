import { Button } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router'

import type { MicroFunPoolKey } from '../../lib/microFun'
import { PlayfulHint } from './PlayfulHint'

type TabEmptyStateAction = {
  label: string
  onClick?: () => void
  href?: string
}

type TabEmptyStateProps = {
  poolKey?: MicroFunPoolKey
  fallback: string
  userId?: string | number | null
  action?: TabEmptyStateAction
  className?: string
}

export function TabEmptyState({
  poolKey,
  fallback,
  userId,
  action,
  className,
}: TabEmptyStateProps) {
  return (
    <div className={`filmony-text-panel py-8 text-center ${className ?? ''}`}>
      {poolKey != null ? (
        <PlayfulHint
          poolKey={poolKey}
          fallback={fallback}
          userId={userId}
          className="text-sm text-(--tgui--hint_color)"
        />
      ) : (
        <p className="text-sm text-(--tgui--hint_color)">{fallback}</p>
      )}
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
