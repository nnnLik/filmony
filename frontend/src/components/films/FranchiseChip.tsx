import { Link } from 'react-router'

import { franchiseChipStyles } from '../../lib/franchiseColor'

export type FranchiseChipProps = {
  franchiseKey: string
  label: string
  size?: 'sm' | 'md'
  className?: string
}

const SIZE_CLASS = {
  sm: 'rounded-md px-1.5 py-0.5 text-[10px] font-medium leading-tight',
  md: 'rounded-lg px-2 py-0.5 text-[11px] font-medium leading-tight',
} as const

export function FranchiseChip({ franchiseKey, label, size = 'sm', className = '' }: FranchiseChipProps) {
  const key = franchiseKey.trim()
  const trimmed = label.trim()
  if (key === '' || trimmed === '') {
    return null
  }

  const styles = franchiseChipStyles(key)

  return (
    <Link
      to={`/franchises/${encodeURIComponent(key)}`}
      className={`inline-flex max-w-full items-center border no-underline outline-none transition-opacity active:opacity-85 focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) ${SIZE_CLASS[size]} ${styles.borderClass} ${styles.backgroundClass} ${className}`.trim()}
      aria-label={`Франшиза: ${trimmed}`}
      onClick={(event) => event.stopPropagation()}
    >
      <span className="truncate text-(--tgui--text_color)">{trimmed}</span>
    </Link>
  )
}
