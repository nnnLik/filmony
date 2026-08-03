type ContrarianBadgeProps = {
  rating: number
  communityAvgRating?: number | null
  isContrarian?: boolean
  className?: string
}

function formatRating(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

export function ContrarianBadge({
  rating,
  communityAvgRating,
  isContrarian = false,
  className = '',
}: ContrarianBadgeProps) {
  if (!isContrarian || communityAvgRating == null || !Number.isFinite(communityAvgRating)) {
    return null
  }

  const tooltip = `Средняя в Filmony: ${formatRating(communityAvgRating)}; ты поставил ${formatRating(rating)}`

  return (
    <span
      className={`inline-flex max-w-[7.5rem] items-center rounded-full border border-[color-mix(in_srgb,#f97316_45%,var(--tgui--divider_color))] bg-[color-mix(in_srgb,#f97316_18%,var(--tgui--secondary_bg_color))] px-1.5 py-0.5 text-[9px] font-semibold uppercase leading-none tracking-wide text-[#fdba74] shadow-sm ${className}`}
      title={tooltip}
      aria-label={tooltip}
    >
      контр
    </span>
  )
}
