import { InlineLoadingState } from './InlineLoadingState'

type PageLoadingStateProps = {
  message?: string
  variant?: 'text' | 'spinner'
  /** Auth gate copy — «Вход…» */
  authPending?: boolean
  className?: string
}

export function PageLoadingState({
  message = 'Загрузка…',
  variant = 'text',
  authPending = false,
  className,
}: PageLoadingStateProps) {
  return (
    <div className={`min-h-dvh ${className ?? ''}`}>
      <InlineLoadingState
        message={authPending ? 'Вход…' : message}
        variant={variant}
        className="py-10"
      />
    </div>
  )
}
