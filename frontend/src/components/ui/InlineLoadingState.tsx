type InlineLoadingStateProps = {
  message?: string
  variant?: 'text' | 'spinner'
  className?: string
}

export function InlineLoadingState({
  message = 'Загрузка…',
  variant = 'text',
  className,
}: InlineLoadingStateProps) {
  if (variant === 'spinner') {
    return (
      <div className={`flex flex-col items-center justify-center gap-3 px-4 py-16 text-center ${className ?? ''}`}>
        <div
          className="size-8 animate-spin rounded-full border-2 border-(--tgui--divider_color) border-t-(--filmony-mint,#5eead4)"
          aria-hidden
        />
        <p className="text-sm text-(--tgui--hint_color)">{message}</p>
      </div>
    )
  }

  return (
    <div className={`px-4 py-16 text-center text-sm text-(--tgui--hint_color) ${className ?? ''}`}>
      <p className="filmony-text-panel inline-block">{message}</p>
    </div>
  )
}
