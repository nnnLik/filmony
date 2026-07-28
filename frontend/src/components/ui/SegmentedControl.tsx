type Segment<T extends string> = {
  value: T
  label: string
  disabled?: boolean
}

type SegmentedControlProps<T extends string> = {
  value: T
  onChange: (value: T) => void
  segments: Segment<T>[]
  ariaLabel: string
  layout?: 'grid' | 'flex'
  gridColsClassName?: string
  size?: 'sm' | 'md'
  className?: string
}

const sizeClasses = {
  sm: 'py-2 text-xs sm:text-sm',
  md: 'py-2.5 text-xs sm:text-sm',
} as const

export function SegmentedControl<T extends string>({
  value,
  onChange,
  segments,
  ariaLabel,
  layout = 'flex',
  gridColsClassName = 'grid-cols-3',
  size = 'md',
  className,
}: SegmentedControlProps<T>) {
  const trackClass =
    layout === 'grid'
      ? `grid ${gridColsClassName} gap-1 rounded-full bg-(--tgui--secondary_bg_color) p-1`
      : 'flex w-full gap-1 rounded-full bg-(--tgui--secondary_bg_color) p-1'

  return (
    <div className={`${trackClass} ${className ?? ''}`} role="tablist" aria-label={ariaLabel}>
      {segments.map((entry) => {
        const selected = value === entry.value
        return (
          <button
            key={entry.value}
            type="button"
            role="tab"
            aria-selected={selected}
            disabled={entry.disabled}
            className={`min-w-0 truncate rounded-full px-1.5 font-medium transition-all active:scale-[0.99] ${sizeClasses[size]} ${
              layout === 'flex' ? 'flex-1' : 'flex items-center justify-center'
            } ${
              selected
                ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                : 'text-(--tgui--hint_color)'
            }`}
            onClick={() => onChange(entry.value)}
          >
            {entry.label}
          </button>
        )
      })}
    </div>
  )
}
