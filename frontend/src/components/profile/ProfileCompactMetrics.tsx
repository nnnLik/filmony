type MetricChip = {
  key: string
  value: number | undefined
  label: string
  onClick?: () => void
}

function shownCount(value: number | undefined): string {
  return typeof value === 'number' ? String(value) : '0'
}

function MetricChipButton({ chip }: { chip: MetricChip }) {
  const content = (
    <>
      <span className="text-sm font-semibold tabular-nums leading-none text-(--tgui--text_color) sm:text-base">
        {shownCount(chip.value)}
      </span>
      <span className="mt-0.5 text-[9px] leading-tight text-(--tgui--hint_color) sm:text-[10px]">{chip.label}</span>
    </>
  )

  if (chip.onClick != null) {
    return (
      <button
        type="button"
        className="flex min-w-[3.25rem] shrink-0 flex-col items-center rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-1.5 outline-none transition-opacity active:opacity-80 focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) sm:min-w-[3.5rem] sm:px-2.5 sm:py-2"
        onClick={chip.onClick}
        aria-label={`${chip.label}: ${shownCount(chip.value)}`}
      >
        {content}
      </button>
    )
  }

  return (
    <div
      className="flex min-w-[3.25rem] shrink-0 flex-col items-center rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) px-2 py-1.5 sm:min-w-[3.5rem] sm:px-2.5 sm:py-2"
      aria-label={`${chip.label}: ${shownCount(chip.value)}`}
    >
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
      className="flex w-full gap-1.5 overflow-x-auto pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      role="list"
      aria-label="Сводка профиля"
    >
      {chips.map((chip) => (
        <div key={chip.key} role="listitem">
          <MetricChipButton chip={chip} />
        </div>
      ))}
    </div>
  )
}
