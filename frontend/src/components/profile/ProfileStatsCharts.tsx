import { Avatar } from '@telegram-apps/telegram-ui'
import { ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'

import type { ProfileInsightItem, SocialTastePeerItem, TagTasteItem } from '../../api/profileTypes'
import { buildConicGradient, type DonutSegmentInput } from '../../lib/statsDonutChart'

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

export function StatsDonutChart({
  segments,
  centerTitle = 'всего',
  onSegmentClick,
  activeValue,
  legendCollapsedTopN,
}: {
  segments: DonutSegmentInput[]
  centerTitle?: string
  onSegmentClick?: (value: string) => void
  activeValue?: string
  legendCollapsedTopN?: number
}) {
  const visibleSegments = segments.filter((segment) => segment.count > 0)
  const [userExpanded, setUserExpanded] = useState(false)

  const canCollapse =
    legendCollapsedTopN != null && visibleSegments.length > legendCollapsedTopN
  const collapsedTopSlice = canCollapse ? visibleSegments.slice(0, legendCollapsedTopN) : visibleSegments
  const activeInCollapsedTop =
    activeValue == null || collapsedTopSlice.some((segment) => segment.value === activeValue)
  const forceExpanded = canCollapse && activeValue != null && !activeInCollapsedTop
  const expanded = userExpanded || forceExpanded

  if (visibleSegments.length === 0) {
    return <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
  }

  const total = visibleSegments.reduce((acc, segment) => acc + segment.count, 0)
  const gradient = buildConicGradient(visibleSegments)
  const legendSegments = canCollapse && !expanded ? collapsedTopSlice : visibleSegments
  const remaining = canCollapse ? visibleSegments.length - (legendCollapsedTopN ?? 0) : 0

  const renderLegendRow = (segment: DonutSegmentInput) => {
    const clickable = onSegmentClick != null && segment.value != null && segment.count > 0
    const active = activeValue != null && segment.value === activeValue
    const row = (
      <>
        <span className="flex min-w-0 items-center gap-2">
          <span
            className="size-2 shrink-0 rounded-full"
            style={{ backgroundColor: segment.color }}
            aria-hidden
          />
          <span
            className={`min-w-0 truncate ${active ? 'font-medium text-(--tgui--text_color)' : 'text-(--tgui--hint_color)'}`}
          >
            {segment.label}
          </span>
        </span>
        <span className="shrink-0 font-semibold tabular-nums text-(--tgui--text_color)">{segment.count}</span>
      </>
    )

    return (
      <li key={`${segment.label}-${segment.value ?? ''}`}>
        {clickable ? (
          <button
            type="button"
            className="flex w-full items-center justify-between gap-2 rounded-lg px-1 py-0.5 text-xs outline-none transition-opacity active:opacity-90 focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) sm:text-sm"
            aria-pressed={active}
            aria-label={`Применить фильтр: ${segment.label}`}
            onClick={() => onSegmentClick(segment.value ?? '')}
          >
            {row}
          </button>
        ) : (
          <div className="flex items-center justify-between gap-2 px-1 py-0.5 text-xs sm:text-sm">{row}</div>
        )}
      </li>
    )
  }

  return (
    <div className="flex w-full min-w-0 flex-col items-center gap-4">
      <div
        className="relative size-28 shrink-0 rounded-full sm:size-32"
        style={{ background: gradient }}
      >
        <div className="absolute inset-3 flex items-center justify-center rounded-full bg-(--tgui--secondary_bg_color) text-center sm:inset-3.5">
          <div>
            <p className="text-[10px] text-(--tgui--hint_color)">{centerTitle}</p>
            <p className="text-lg font-bold tabular-nums sm:text-xl">{total}</p>
          </div>
        </div>
      </div>
      <ul className="grid w-full min-w-0 max-w-[18rem] gap-1.5 sm:max-w-none">
        {legendSegments.map(renderLegendRow)}
        {canCollapse && !expanded ? (
          <li>
            <button
              type="button"
              className="w-full rounded-lg px-1 py-1 text-xs text-(--tgui--link_color) outline-none transition-opacity active:opacity-90 focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) sm:text-sm"
              onClick={() => setUserExpanded(true)}
            >
              Ещё {remaining}
            </button>
          </li>
        ) : null}
        {canCollapse && expanded && !forceExpanded ? (
          <li>
            <button
              type="button"
              className="w-full rounded-lg px-1 py-1 text-xs text-(--tgui--link_color) outline-none transition-opacity active:opacity-90 focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) sm:text-sm"
              onClick={() => setUserExpanded(false)}
            >
              Свернуть
            </button>
          </li>
        ) : null}
      </ul>
    </div>
  )
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

const TAG_BUBBLE_COLORS = [
  'bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_22%,transparent)]',
  'bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_20%,transparent)]',
  'bg-[color-mix(in_srgb,#4f87ff_18%,transparent)]',
  'bg-[color-mix(in_srgb,#ef7d9b_16%,transparent)]',
]

function tagBubbleSize(count: number, max: number): string {
  if (max <= 0) return 'text-[10px] px-2 py-0.5'
  const ratio = count / max
  if (ratio >= 0.75) return 'text-sm px-3 py-1.5'
  if (ratio >= 0.45) return 'text-xs px-2.5 py-1'
  return 'text-[10px] px-2 py-0.5'
}

export function TagBubbleChart({
  items,
  onTagClick,
  selectedTags,
}: {
  items: TagTasteItem[]
  onTagClick?: (tag: string) => void
  selectedTags?: readonly string[]
}) {
  if (items.length === 0) {
    return <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
  }

  const maxCount = Math.max(...items.map((t) => t.weight ?? t.count), 1)
  const selected = new Set(selectedTags ?? [])

  return (
    <div className="flex flex-wrap items-center justify-center gap-2 py-1">
      {items.map((item, idx) => {
        const sizeClass = tagBubbleSize(item.weight ?? item.count, maxCount)
        const hilite = selected.has(item.tag)
        const colorClass = TAG_BUBBLE_COLORS[idx % TAG_BUBBLE_COLORS.length]
        const label =
          item.average_rating != null
            ? `${item.tag} · ${item.average_rating.toFixed(1)}`
            : item.avg_rating != null
              ? `${item.tag} · ${item.avg_rating.toFixed(1)}`
              : item.tag

        const inner = (
          <>
            <span className="font-medium">{label}</span>
            <span className="ml-1 text-(--tgui--hint_color)">({item.count})</span>
          </>
        )

        if (onTagClick != null) {
          return (
            <button
              key={item.tag}
              type="button"
              aria-pressed={hilite}
              aria-label={`Фильтр по тегу «${item.tag}»`}
              className={`rounded-full border outline-none transition-opacity active:opacity-90 focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) ${sizeClass} ${
                hilite
                  ? 'border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_55%,transparent)] text-(--tgui--text_color)'
                  : `border-(--tgui--divider_color) ${colorClass} text-(--tgui--text_color)`
              }`}
              onClick={() => onTagClick(item.tag)}
            >
              {inner}
            </button>
          )
        }

        return (
          <span
            key={item.tag}
            className={`rounded-full border border-(--tgui--divider_color) ${colorClass} ${sizeClass} text-(--tgui--text_color)`}
          >
            {inner}
          </span>
        )
      })}
    </div>
  )
}

type FlowSegment = { label: string; count: number; value?: string }

export function TasteFlowStrip({
  segments,
  onSegmentClick,
  activeValue,
}: {
  segments: FlowSegment[]
  onSegmentClick?: (value: string) => void
  activeValue?: string
}) {
  if (segments.length === 0) {
    return <p className="text-sm text-(--tgui--hint_color)">Пока нет данных</p>
  }

  const max = Math.max(...segments.map((s) => s.count), 1)

  return (
    <div className="flex w-full min-w-0 flex-col gap-2">
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-(--tgui--bg_color)">
        {segments.map((seg, segIdx) => {
          const widthPct = max > 0 ? (seg.count / segments.reduce((a, s) => a + s.count, 0)) * 100 : 0
          if (widthPct <= 0) return null
          const hues = ['#5de1d4', '#4f87ff', '#e8b86d', '#ef7d9b']
          const hue = hues[segIdx % hues.length]
          return (
            <div
              key={seg.label}
              className="h-full min-w-px transition-[width]"
              style={{ width: `${Math.max(widthPct, seg.count > 0 ? 6 : 0)}%`, backgroundColor: hue }}
              title={`${seg.label}: ${seg.count}`}
            />
          )
        })}
      </div>
      <ul className="grid gap-1.5">
        {segments.map((seg) => {
          const clickable = onSegmentClick != null && seg.value != null && seg.count > 0
          const active = activeValue != null && seg.value === activeValue
          const row = (
            <>
              <span className={`min-w-0 truncate ${active ? 'text-(--tgui--text_color)' : 'text-(--tgui--hint_color)'}`}>
                {seg.label}
              </span>
              <span className="shrink-0 font-semibold tabular-nums text-(--tgui--text_color)">{seg.count}</span>
            </>
          )
          return (
            <li key={seg.label}>
              {clickable ? (
                <button
                  type="button"
                  className="flex w-full items-center justify-between gap-2 rounded-lg px-1 py-0.5 text-xs outline-none transition-opacity active:opacity-90 focus-visible:ring-2 focus-visible:ring-(--tgui--link_color) sm:text-sm"
                  onClick={() => onSegmentClick(seg.value ?? '')}
                >
                  {row}
                </button>
              ) : (
                <div className="flex items-center justify-between gap-2 px-1 py-0.5 text-xs sm:text-sm">{row}</div>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export function ProfileInsightsGrid({ items }: { items: ProfileInsightItem[] }) {
  if (items.length === 0) return null

  const cardClassName =
    'min-w-0 rounded-xl border border-[color-mix(in_srgb,var(--tgui--divider_color)_72%,transparent)] bg-(--tgui--bg_color) px-2.5 py-2 sm:px-3'

  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map((item) => {
        const content = (
          <>
            <p className="truncate text-[10px] font-medium text-(--tgui--hint_color)">{item.label}</p>
            <p className="mt-0.5 text-base font-semibold tabular-nums text-(--tgui--text_color) sm:text-lg">{item.value}</p>
            {item.hint != null && item.hint !== '' ? (
              <p className="mt-0.5 truncate text-[10px] text-(--tgui--hint_color)">{item.hint}</p>
            ) : null}
          </>
        )

        if (item.to != null && item.to !== '') {
          return (
            <Link
              key={item.key}
              to={item.to}
              className={`${cardClassName} block no-underline outline-none transition-[background-color,transform] hover:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] active:scale-[0.998] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-(--tgui--link_color)`}
            >
              {content}
            </Link>
          )
        }

        return (
          <div key={item.key} className={cardClassName}>
            {content}
          </div>
        )
      })}
    </div>
  )
}

function peerDisplayName(peer: SocialTastePeerItem): string {
  if (peer.display_name?.trim()) return peer.display_name.trim()
  return peer.profile_slug
}

function peerInitials(peer: SocialTastePeerItem): string {
  const name = peerDisplayName(peer)
  const parts = name.split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return (parts[0].slice(0, 1) + parts[1].slice(0, 1)).toUpperCase()
  return name.slice(0, 2).toUpperCase()
}

function formatBreakdownPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

function TastePeerBreakdown({ peer }: { peer: SocialTastePeerItem }) {
  const [open, setOpen] = useState(false)
  const breakdown = peer.breakdown

  return (
    <div className="border-t border-(--tgui--divider_color) px-3 pb-2">
      <button
        type="button"
        className="flex w-full items-center justify-between py-2 text-left text-[11px] text-(--tgui--hint_color)"
        onClick={(event) => {
          event.preventDefault()
          event.stopPropagation()
          setOpen((prev) => !prev)
        }}
        aria-expanded={open}
      >
        <span>
          Совпадение v2: <span className="font-semibold text-(--tgui--link_color)">{formatBreakdownPercent(peer.score_v2)}</span>
        </span>
        <ChevronDown
          className={`block size-4 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden
        />
      </button>
      {open ? (
        <dl className="grid grid-cols-2 gap-x-3 gap-y-1 pb-1 text-[10px] text-(--tgui--hint_color)">
          <div>
            <dt>Общие тайтлы</dt>
            <dd className="font-semibold tabular-nums text-(--tgui--text_color)">
              {formatBreakdownPercent(breakdown.shared_titles)}
            </dd>
          </div>
          <div>
            <dt>Теги</dt>
            <dd className="font-semibold tabular-nums text-(--tgui--text_color)">
              {formatBreakdownPercent(breakdown.tag_overlap)}
            </dd>
          </div>
          <div>
            <dt>Близость оценок</dt>
            <dd className="font-semibold tabular-nums text-(--tgui--text_color)">
              {formatBreakdownPercent(breakdown.rating_agreement)}
            </dd>
          </div>
          <div>
            <dt>Избранное</dt>
            <dd className="font-semibold tabular-nums text-(--tgui--text_color)">
              {formatBreakdownPercent(breakdown.shared_favorites)}
            </dd>
          </div>
        </dl>
      ) : null}
    </div>
  )
}

export function SocialTastePeers({ peers }: { peers: SocialTastePeerItem[] }) {
  if (peers.length === 0) {
    return <p className="text-sm text-(--tgui--hint_color)">Пока нет похожих профилей</p>
  }

  return (
    <ul className="divide-y divide-(--tgui--divider_color) overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color)">
      {peers.map((peer) => (
        <li key={peer.id}>
          <Link
            to={`/u/${encodeURIComponent(peer.id)}`}
            className="flex items-center gap-3 px-3 py-2.5 no-underline outline-none transition-[background-color] hover:bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_88%,transparent)] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-(--tgui--link_color)"
          >
            <Avatar src={peer.photo_url ?? undefined} acronym={peerInitials(peer)} size={36} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm text-(--tgui--text_color)">{peerDisplayName(peer)}</p>
              <p className="font-mono text-[10px] text-(--tgui--hint_color)">@{peer.profile_slug}</p>
            </div>
            <div className="shrink-0 text-right text-[10px] tabular-nums text-(--tgui--hint_color)">
              <span className="block font-semibold text-(--tgui--link_color)">
                {Math.round(peer.score_v2 * 100)}%
              </span>
              <span>{peer.shared_films_count} общих</span>
            </div>
          </Link>
          <TastePeerBreakdown peer={peer} />
        </li>
      ))}
    </ul>
  )
}
