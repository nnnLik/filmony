type MetricChip = {
  key: string
  value: number | undefined
  label: string
  onClick?: () => void
}

function shownCount(value: number | undefined): string {
  return typeof value === 'number' ? String(value) : '0'
}

const METRIC_CHIP_CLASS =
  'flex w-full flex-col items-center justify-center rounded-xl bg-(--tgui--secondary_bg_color) px-1 py-2'

function MetricChipButton({ chip }: { chip: MetricChip }) {
  const content = (
    <>
      <span className="text-[15px] font-semibold tabular-nums leading-none text-(--tgui--text_color)">
        {shownCount(chip.value)}
      </span>
      <span className="mt-1 w-full truncate text-center text-[10px] leading-tight text-(--tgui--hint_color)">
        {chip.label}
      </span>
    </>
  )

  if (chip.onClick != null) {
    return (
      <button
        type="button"
        className={`${METRIC_CHIP_CLASS} outline-none transition-colors active:bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_10%,var(--tgui--secondary_bg_color))] focus-visible:ring-2 focus-visible:ring-(--tgui--link_color)`}
        onClick={chip.onClick}
        aria-label={`${chip.label}: ${shownCount(chip.value)}`}
      >
        {content}
      </button>
    )
  }

  return (
    <div className={METRIC_CHIP_CLASS} aria-label={`${chip.label}: ${shownCount(chip.value)}`}>
      {content}
    </div>
  )
}

export type ProfileCompactMetricsProps = {
  followers_count?: number
  following_count?: number
  cards_count?: number
  watchlist_count?: number
  favorites_count?: number
  onFollowersClick?: () => void
  onFollowingClick?: () => void
  onRatedClick?: () => void
  onWatchlistClick?: () => void
  onFavoritesClick?: () => void
}

export function ProfileCompactMetrics({
  followers_count,
  following_count,
  cards_count,
  watchlist_count,
  favorites_count,
  onFollowersClick,
  onFollowingClick,
  onRatedClick,
  onWatchlistClick,
  onFavoritesClick,
}: ProfileCompactMetricsProps) {
  const chips: MetricChip[] = [
    { key: 'followers', value: followers_count, label: 'подписч.', onClick: onFollowersClick },
    { key: 'following', value: following_count, label: 'подписок', onClick: onFollowingClick },
    { key: 'rated', value: cards_count, label: 'оценено', onClick: onRatedClick },
    { key: 'later', value: watchlist_count, label: 'позже', onClick: onWatchlistClick },
    { key: 'favorites', value: favorites_count, label: 'любимые', onClick: onFavoritesClick },
  ]

  return (
    <div
      className="grid w-full grid-cols-5 gap-1.5"
      role="list"
      aria-label="Сводка профиля"
    >
      {chips.map((chip) => (
        <div key={chip.key} role="listitem" className="min-w-0">
          <MetricChipButton chip={chip} />
        </div>
      ))}
    </div>
  )
}
