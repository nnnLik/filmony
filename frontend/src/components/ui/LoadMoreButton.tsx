import { Button } from '@telegram-apps/telegram-ui'

type LoadMoreButtonProps = {
  onClick: () => void
  busy?: boolean
  className?: string
}

export function LoadMoreButton({ onClick, busy = false, className }: LoadMoreButtonProps) {
  return (
    <Button
      stretched
      mode="gray"
      className={className}
      disabled={busy}
      onClick={() => {
        onClick()
      }}
    >
      {busy ? 'Подгружаем…' : 'Подгрузить ещё'}
    </Button>
  )
}
