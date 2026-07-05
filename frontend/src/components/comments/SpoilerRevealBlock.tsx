import { useState, type ReactNode } from 'react'

const SPOILER_BUTTON_CLASS =
  'mx-0.5 inline rounded-md border border-[color-mix(in_srgb,var(--tgui--hint_color)_45%,transparent)] bg-[color-mix(in_srgb,var(--tgui--hint_color)_16%,transparent)] px-1.5 py-0.5 align-[-0.12em] text-[0.92em] font-medium text-(--tgui--hint_color) transition-opacity hover:opacity-95 active:opacity-90'

type SpoilerRevealBlockProps = {
  children: ReactNode
  className?: string
}

export function SpoilerRevealBlock({ children, className }: SpoilerRevealBlockProps) {
  const [revealed, setRevealed] = useState(false)

  if (revealed) {
    return (
      <span className={className}>
        <span className="rounded-md bg-[color-mix(in_srgb,var(--tgui--hint_color)_10%,transparent)] px-0.5">
          {children}
        </span>
      </span>
    )
  }

  return (
    <button
      type="button"
      className={SPOILER_BUTTON_CLASS}
      aria-label="Показать спойлер"
      onClick={(e) => {
        e.stopPropagation()
        setRevealed(true)
      }}
    >
      Спойлер · нажмите, чтобы показать
    </button>
  )
}
