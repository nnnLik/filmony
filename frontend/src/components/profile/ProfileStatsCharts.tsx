type BarItem = { label: string; count: number }

const BAR_TRACK = 'rounded-full bg-(--tgui--bg_color)'
const BAR_FILL = 'rounded-full bg-[linear-gradient(90deg,#52d6c7_0%,#72efe4_100%)]'

const BAR_ROW_GRID =
  'grid w-full min-w-0 grid-cols-[minmax(2rem,3rem)_minmax(0,1fr)_2.25rem] items-center gap-2 sm:grid-cols-[minmax(2.25rem,3.25rem)_minmax(0,1fr)_2.5rem]'

export function StatsDistributionBars({
  items,
  maxCount,
  onItemActivate,
  itemActionHint,
}: {
  items: BarItem[]
  maxCount: number
  /** Если задано, сегменты с count > 0 становятся кнопками (например, фильтр по году). */
  onItemActivate?: (label: string) => void
  /** Доступное имя действия для строк с count &gt; 0, если нужен общий шаблон (добавляется к подписи сегмента). */
  itemActionHint?: string
}) {
  const safeMax = maxCount > 0 ? maxCount : 0

  return (
    <div className="flex w-full min-w-0 flex-col gap-2.5">
      {items.map((item) => {
        const pct = safeMax > 0 ? Math.min(100, (item.count / safeMax) * 100) : 0
        const showBar = item.count > 0
        const clickable = Boolean(onItemActivate) && item.count > 0
        const actionLabel =
          itemActionHint != null && itemActionHint !== ''
            ? `${itemActionHint}: ${item.label}`
            : `Применить фильтр: ${item.label}`

        const rowInner = (
          <>
            <span className="text-center text-[11px] font-medium tabular-nums text-(--tgui--hint_color) sm:text-xs">
              {item.label}
            </span>
            <div className={`relative h-2.5 w-full min-w-0 overflow-hidden ${BAR_TRACK}`}>
              {showBar ? (
                <div
                  className={`h-full min-w-px ${BAR_FILL}`}
                  style={{ width: `${Math.max(pct, item.count > 0 ? 8 : 0)}%` }}
                />
              ) : null}
            </div>
            <span className="text-right text-[11px] tabular-nums text-(--tgui--text_color) sm:text-xs">{item.count}</span>
          </>
        )

        return clickable ? (
          <button
            key={item.label}
            type="button"
            className={`${BAR_ROW_GRID} cursor-pointer rounded-lg text-left outline-none transition-opacity hover:opacity-95 active:opacity-90 focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) focus-visible:ring-offset-2 focus-visible:ring-offset-(--tgui--secondary_bg_color)`}
            aria-label={actionLabel}
            onClick={() => onItemActivate?.(item.label)}
          >
            {rowInner}
          </button>
        ) : (
          <div key={item.label} className={BAR_ROW_GRID}>
            {rowInner}
          </div>
        )
      })}
    </div>
  )
}

type SentimentParts = {
  low: number
  mid: number
  high: number
  total: number
  midPct: number
  highPct: number
}

export function TastePolarityChart({ sentiment }: { sentiment: SentimentParts }) {
  const { low, mid, high, total, midPct, highPct } = sentiment

  return (
    <div className="flex w-full min-w-0 flex-col items-center gap-4">
      <div
        className="relative size-28 shrink-0 rounded-full sm:size-32"
        style={{
          background: `conic-gradient(#5de1d4 0% ${highPct}%, #4f87ff ${highPct}% ${highPct + midPct}%, #ef7d9b ${
            highPct + midPct
          }% 100%)`,
        }}
      >
        <div className="absolute inset-3 flex items-center justify-center rounded-full bg-(--tgui--secondary_bg_color) text-center sm:inset-3.5">
          <div>
            <p className="text-[10px] text-(--tgui--hint_color)">всего</p>
            <p className="text-lg font-bold tabular-nums sm:text-xl">{total}</p>
          </div>
        </div>
      </div>
      <div className="flex w-full min-w-0 max-w-[16rem] items-center justify-center gap-6 text-[11px] tabular-nums sm:max-w-none sm:gap-8">
        <div className="flex flex-col items-center gap-1">
          <span className="h-2 w-6 rounded-full bg-[#ef7d9b]" aria-hidden />
          <span className="text-(--tgui--text_color)">{low}</span>
        </div>
        <div className="flex flex-col items-center gap-1">
          <span className="h-2 w-6 rounded-full bg-[#4f87ff]" aria-hidden />
          <span className="text-(--tgui--text_color)">{mid}</span>
        </div>
        <div className="flex flex-col items-center gap-1">
          <span className="h-2 w-6 rounded-full bg-[#5de1d4]" aria-hidden />
          <span className="text-(--tgui--text_color)">{high}</span>
        </div>
      </div>
    </div>
  )
}
