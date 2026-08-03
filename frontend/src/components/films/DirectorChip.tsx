import { Link } from 'react-router'

import { directorChipStyles } from '../../lib/directorColor'

export type DirectorChipProps = {
  kinopoiskId: number
  name: string
  size?: 'sm' | 'md'
  className?: string
}

const SIZE_CLASS = {
  sm: 'rounded-md px-1.5 py-0.5 text-[10px] font-medium leading-tight',
  md: 'rounded-lg px-2 py-0.5 text-[11px] font-medium leading-tight',
} as const

export function DirectorChip({ kinopoiskId, name, size = 'sm', className = '' }: DirectorChipProps) {
  const trimmed = name.trim()
  if (!Number.isInteger(kinopoiskId) || kinopoiskId < 1 || trimmed === '') {
    return null
  }

  const styles = directorChipStyles(kinopoiskId)

  return (
    <Link
      to={`/directors/${kinopoiskId}`}
      className={`inline-flex max-w-full items-center border no-underline outline-none transition-opacity active:opacity-85 focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) ${SIZE_CLASS[size]} ${styles.borderClass} ${styles.backgroundClass} ${className}`.trim()}
      aria-label={`Режиссёр: ${trimmed}`}
      onClick={(event) => event.stopPropagation()}
    >
      <span className="truncate text-(--tgui--text_color)">{trimmed}</span>
    </Link>
  )
}
