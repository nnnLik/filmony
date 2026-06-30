import { CalendarClock } from 'lucide-react'

type PlannedCardBadgeVariant = 'ribbon' | 'inline'

type PlannedCardBadgeProps = {
  variant?: PlannedCardBadgeVariant
  className?: string
}

const LABEL = 'Запланировано'

export function PlannedCardBadge({ variant = 'inline', className = '' }: PlannedCardBadgeProps) {
  if (variant === 'ribbon') {
    return (
      <span
        className={[
          'inline-flex shrink-0 items-center gap-1 rounded-md border border-[color-mix(in_srgb,#6366f1_48%,transparent)] bg-[color-mix(in_srgb,#6366f1_16%,transparent)] px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-indigo-600 dark:text-indigo-300',
          className,
        ]
          .filter(Boolean)
          .join(' ')}
        title="Запланированный просмотр"
      >
        <CalendarClock className="block size-3 shrink-0" strokeWidth={2.25} aria-hidden />
        {LABEL}
      </span>
    )
  }

  return (
    <span
      className={[
        'inline-flex shrink-0 items-center gap-1 rounded-md border border-[color-mix(in_srgb,#6366f1_40%,transparent)] bg-[color-mix(in_srgb,#6366f1_12%,transparent)] px-2 py-0.5 text-[10px] font-semibold tracking-wide text-indigo-600 dark:text-indigo-300',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      aria-label={LABEL}
    >
      <CalendarClock className="block size-3 shrink-0" strokeWidth={2.25} aria-hidden />
      {LABEL}
    </span>
  )
}
