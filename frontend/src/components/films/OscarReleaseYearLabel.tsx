import { Trophy } from 'lucide-react'

import {
  isOscarWinnerBadge,
  oscarBadgeAriaLabel,
  oscarBadgeTitle,
  type FilmAwardBadgeLike,
} from '../../lib/filmAwardBadgeDisplay'

export type OscarReleaseYearVariant = 'overlay' | 'inline' | 'compact'

type OscarReleaseYearLabelProps = {
  label: string
  badge?: FilmAwardBadgeLike | null
  releaseYear?: number | null
  variant?: OscarReleaseYearVariant
  className?: string
}

const variantClasses: Record<
  OscarReleaseYearVariant,
  { plain: string; winner: string; nominee: string; icon: string }
> = {
  overlay: {
    plain: 'font-normal text-white/72',
    winner:
      'inline-flex items-center gap-0.5 rounded-md border border-[color-mix(in_srgb,#eab308_55%,transparent)] bg-[color-mix(in_srgb,#eab308_22%,transparent)] px-1 py-0.5 text-[13px] font-semibold tabular-nums text-[#fde68a]',
    nominee:
      'inline-flex items-center gap-0.5 rounded-md border border-white/35 bg-black/25 px-1 py-0.5 text-[13px] font-semibold tabular-nums text-white/85',
    icon: 'size-3',
  },
  inline: {
    plain: 'text-xs font-medium tabular-nums text-(--tgui--hint_color) sm:text-sm',
    winner:
      'inline-flex items-center gap-0.5 rounded-md border border-[color-mix(in_srgb,#eab308_45%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,#eab308_16%,var(--tgui--secondary_bg_color))] px-1.5 py-0.5 text-xs font-semibold tabular-nums text-[#facc15] sm:text-sm',
    nominee:
      'inline-flex items-center gap-0.5 rounded-md border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-1.5 py-0.5 text-xs font-semibold tabular-nums text-(--tgui--hint_color) sm:text-sm',
    icon: 'size-3.5',
  },
  compact: {
    plain: 'text-xs tabular-nums text-(--tgui--hint_color)',
    winner:
      'inline-flex items-center gap-0.5 rounded-md border border-[color-mix(in_srgb,#eab308_45%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,#eab308_16%,var(--tgui--secondary_bg_color))] px-1 py-0.5 text-[10px] font-semibold tabular-nums text-[#facc15]',
    nominee:
      'inline-flex items-center gap-0.5 rounded-md border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-1 py-0.5 text-[10px] font-semibold tabular-nums text-(--tgui--hint_color)',
    icon: 'size-3',
  },
}

export function OscarReleaseYearLabel({
  label,
  badge = null,
  releaseYear = null,
  variant = 'inline',
  className = '',
}: OscarReleaseYearLabelProps) {
  const styles = variantClasses[variant]

  if (badge == null) {
    return <span className={`${styles.plain} ${className}`.trim()}>{label}</span>
  }

  const isWinner = isOscarWinnerBadge(badge)
  const styledClass = isWinner ? styles.winner : styles.nominee
  const a11y = oscarBadgeAriaLabel(badge, releaseYear)
  const title = oscarBadgeTitle(badge, releaseYear)

  return (
    <span
      className={`${styledClass} ${className}`.trim()}
      title={title}
      aria-label={a11y}
    >
      <Trophy
        className={`block shrink-0 ${styles.icon} ${isWinner ? 'text-[#facc15]' : variant === 'overlay' ? 'text-white/85' : 'text-(--tgui--hint_color)'}`}
        aria-hidden
      />
      <span>{label}</span>
    </span>
  )
}

type OscarReleaseYearRowProps = {
  label: string
  badges: FilmAwardBadgeLike[]
  releaseYear?: number | null
  variant?: OscarReleaseYearVariant
  className?: string
}

/** One styled year label per Oscar badge (detail surfaces). */
export function OscarReleaseYearRow({
  label,
  badges,
  releaseYear = null,
  variant = 'inline',
  className = '',
}: OscarReleaseYearRowProps) {
  if (badges.length === 0) {
    return (
      <OscarReleaseYearLabel
        label={label}
        releaseYear={releaseYear}
        variant={variant}
        className={className}
      />
    )
  }

  return (
    <span className={`inline-flex flex-wrap items-center gap-1.5 ${className}`.trim()}>
      {badges.map((badge) => (
        <OscarReleaseYearLabel
          key={`${badge.kind}-${badge.ceremony_year}`}
          label={label}
          badge={badge}
          releaseYear={releaseYear}
          variant={variant}
        />
      ))}
    </span>
  )
}
