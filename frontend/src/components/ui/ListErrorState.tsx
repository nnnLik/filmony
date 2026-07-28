import { Button } from '@telegram-apps/telegram-ui'

type ListErrorStateProps = {
  message: string
  onRetry?: () => void
}

export function ListErrorState({ message, onRetry }: ListErrorStateProps) {
  return (
    <div className="rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] px-4 py-4">
      <p className="text-[14px] text-(--tgui--hint_color)">{message}</p>
      {onRetry != null ? (
        <Button stretched className="mt-4" onClick={onRetry}>
          Повторить
        </Button>
      ) : null}
    </div>
  )
}
