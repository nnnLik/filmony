type MetricItem = {
  key: string
  value: number | undefined
  label: string
  onClick?: () => void
}

function shownCount(value: number | undefined): string {
  return typeof value === 'number' ? String(value) : '0'
}

const METRIC_TEXT_BUTTON_CLASS =
  'inline-flex min-h-8 items-center rounded-md px-0.5 py-1 text-left outline-none transition-opacity active:opacity-70 focus-visible:ring-2 focus-visible:ring-(--tgui--link_color)'

function MetricTextItem({ item }: { item: MetricItem }) {
  const content = (
    <>
      <span className="font-semibold tabular-nums text-(--tgui--text_color)">{shownCount(item.value)}</span>
      <span className="text-(--tgui--hint_color)"> {item.label}</span>
    </>
  )

  if (item.onClick != null) {
    return (
      <button
        type="button"
        className={METRIC_TEXT_BUTTON_CLASS}
        onClick={item.onClick}
        aria-label={`${item.label}: ${shownCount(item.value)}`}
      >
        {content}
      </button>
    )
  }

  return (
    <span className="inline-flex min-h-8 items-center py-1" aria-label={`${item.label}: ${shownCount(item.value)}`}>
      {content}
    </span>
  )
}

function MetricTextRow({ items }: { items: MetricItem[] }) {
  return (
    <div className="flex flex-wrap items-center gap-x-1 gap-y-0.5 text-[13px] leading-snug">
      {items.map((item, index) => (
        <span key={item.key} className="inline-flex items-center gap-x-1">
          {index > 0 ? <span className="select-none text-(--tgui--hint_color)">·</span> : null}
          <MetricTextItem item={item} />
        </span>
      ))}
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
  const socialItems: MetricItem[] = [
    { key: 'followers', value: followers_count, label: 'подписчиков', onClick: onFollowersClick },
    { key: 'following', value: following_count, label: 'подписок', onClick: onFollowingClick },
  ]

  const libraryItems: MetricItem[] = [
    { key: 'rated', value: cards_count, label: 'оценено', onClick: onRatedClick },
    { key: 'later', value: watchlist_count, label: 'позже', onClick: onWatchlistClick },
    { key: 'favorites', value: favorites_count, label: 'любимые', onClick: onFavoritesClick },
  ]

  return (
    <div className="mt-2 flex flex-col gap-1" role="list" aria-label="Сводка профиля">
      <div role="listitem">
        <MetricTextRow items={socialItems} />
      </div>
      <div role="listitem">
        <MetricTextRow items={libraryItems} />
      </div>
    </div>
  )
}
