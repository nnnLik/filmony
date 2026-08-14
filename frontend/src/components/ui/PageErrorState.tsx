import { Button } from '@telegram-apps/telegram-ui'
import { Link } from 'react-router'

type PageErrorStateProps = {
  title?: string
  message: string
  onRetry?: () => void
  backLabel?: string
  backHref?: string
  className?: string
}

export function PageErrorState({
  title,
  message,
  onRetry,
  backLabel,
  backHref,
  className,
}: PageErrorStateProps) {
  return (
    <div className={`flex min-h-dvh flex-col items-center justify-center gap-4 px-4 py-10 ${className ?? ''}`}>
      <div className="w-full max-w-md rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_92%,transparent)] px-4 py-6 text-center">
        {title != null ? (
          <p className="mb-2 text-[16px] font-semibold text-(--tgui--text_color)">{title}</p>
        ) : null}
        <p className="text-[14px] leading-relaxed text-(--tgui--destructive_text_color)">{message}</p>
        {onRetry != null ? (
          <Button stretched className="mt-4" onClick={onRetry}>
            Повторить
          </Button>
        ) : null}
        {backHref != null && backLabel != null ? (
          <Link to={backHref} className="mt-3 block no-underline">
            <Button stretched mode="gray">
              {backLabel}
            </Button>
          </Link>
        ) : null}
      </div>
    </div>
  )
}
