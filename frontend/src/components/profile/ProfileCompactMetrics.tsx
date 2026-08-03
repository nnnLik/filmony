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
  'flex min-w-[3.5rem] flex-col items-center rounded-xl border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_28%,var(--tgui--divider_color))] bg-(--tgui--secondary_bg_color) px-3 py-2 shadow-[0_0_0_1px_color-mix(in_srgb,var(--filmony-mint,#5eead4)_8%,transparent),0_4px_14px_color-mix(in_srgb,var(--filmony-mint,#5eead4)_6%,transparent)] sm:min-w-[4rem] sm:px-3.5 sm:py-2.5'

function MetricChipButton({ chip }: { chip: MetricChip }) {
  const content = (
    <>
      <span className="text-base font-bold tabular-nums leading-none text-(--tgui--text_color) sm:text-lg">
        {shownCount(chip.value)}
      </span>
      <span className="mt-1 text-[10px] leading-tight text-(--tgui--hint_color) sm:text-[11px]">{chip.label}</span>
    </>
  )

  if (chip.onClick != null) {
    return (
      <button
        type="button"
        className={`${METRIC_CHIP_CLASS} outline-none transition-opacity active:opacity-80 focus-visible:ring-2 focus-visible:ring-(--tgui--link_color)`}
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
      className="grid w-full grid-cols-5 justify-items-center gap-3 max-[380px]:grid-cols-3 max-[380px]:gap-2"
      role="list"
      aria-label="Сводка профиля"
    >
      {chips.map((chip) => (
        <div key={chip.key} role="listitem" className="w-full max-w-[5.5rem]">
          <MetricChipButton chip={chip} />
        </div>
      ))}
    </div>
  )
}
