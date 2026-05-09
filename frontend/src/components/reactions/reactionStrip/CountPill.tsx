import { Avatar } from '@telegram-apps/telegram-ui'
import { useEffect, useRef, useState } from 'react'

import type { ReactionActor } from '../../../api/profileTypes'
import { loadReactionActors } from '../../../lib/reactionActorsCache'
import { displayActorName } from './displayActorName'
import { ReactionThumb } from './ReactionThumb'

export type CountPillProps = {
  targetKind: 'movie_card' | 'movie_card_comment'
  targetId: number
  reactionTypeId: number
  disabled: boolean
  mine: boolean
  imageUrl: string
  assetKey: string
  count: number
  onPick: () => void
  compact: boolean
  /** Уменьшенные пиллы вместе с ``compact`` (шапка карточки на детальной странице). */
  pillTight?: boolean
}

export function CountPill({
  targetKind,
  targetId,
  reactionTypeId,
  disabled,
  mine,
  imageUrl,
  assetKey,
  count,
  onPick,
  compact,
  pillTight = false,
}: CountPillProps) {
  const [hover, setHover] = useState(false)
  const [actors, setActors] = useState<ReactionActor[] | null>(null)
  const [actorsErr, setActorsErr] = useState<string | null>(null)
  const timer = useRef<number | null>(null)

  useEffect(() => {
    if (!hover) {
      if (timer.current != null) window.clearTimeout(timer.current)
      timer.current = null
      return
    }
    timer.current = window.setTimeout(() => {
      setActorsErr(null)
      setActors(null)
      void (async () => {
        try {
          const rows = await loadReactionActors({
            targetKind,
            targetId,
            reactionTypeId,
          })
          setActors(rows)
        } catch {
          setActorsErr('err')
        }
      })()
    }, 220)
    return () => {
      if (timer.current != null) window.clearTimeout(timer.current)
    }
  }, [hover, reactionTypeId, targetId, targetKind])

  const showBubble = hover && (actors !== null || actorsErr !== null)
  const titleTip =
    assetKey.includes('/') || assetKey.includes('\\')
      ? assetKey.replace(/\\/g, '/').split('/').filter(Boolean).pop() ?? assetKey
      : assetKey

  return (
    <div
      className="relative shrink-0"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => {
        setHover(false)
        setActors(null)
        setActorsErr(null)
      }}
    >
      <button
        type="button"
        disabled={disabled}
        onClick={onPick}
        className={
          compact && pillTight
            ? `inline-flex h-9 min-h-9 cursor-pointer touch-manipulation items-center gap-1 rounded-full px-1.5 py-px text-[13px] leading-none tabular-nums ring-[0.5px] transition-[transform,opacity] active:scale-[0.97] disabled:opacity-50 ${
                mine
                  ? 'bg-[color-mix(in_srgb,var(--tgui--link_color)_14%,var(--tgui--secondary_bg_color))] ring-[color-mix(in_srgb,var(--tgui--link_color)_32%,transparent)]'
                  : 'bg-[color-mix(in_srgb,var(--tgui--hint_color)_06%,var(--tgui--secondary_bg_color))] ring-[color-mix(in_srgb,var(--tgui--divider_color)_38%,transparent)]'
              }`
            : compact
              ? `inline-flex h-10 min-h-10 cursor-pointer touch-manipulation items-center gap-1.5 rounded-full px-1.5 py-px text-[14px] leading-none tabular-nums ring-[0.5px] transition-[transform,opacity] active:scale-[0.97] disabled:opacity-50 ${
                  mine
                    ? 'bg-[color-mix(in_srgb,var(--tgui--link_color)_14%,var(--tgui--secondary_bg_color))] ring-[color-mix(in_srgb,var(--tgui--link_color)_32%,transparent)]'
                    : 'bg-[color-mix(in_srgb,var(--tgui--hint_color)_06%,var(--tgui--secondary_bg_color))] ring-[color-mix(in_srgb,var(--tgui--divider_color)_38%,transparent)]'
                }`
              : `inline-flex h-[22px] min-h-[22px] cursor-pointer touch-manipulation items-center gap-0.5 rounded-full px-1 py-px text-[10px] leading-none tabular-nums ring-1 transition-[transform,opacity] active:scale-[0.98] disabled:opacity-50 ${
                  mine
                    ? 'bg-[color-mix(in_srgb,var(--tgui--link_color)_18%,var(--tgui--secondary_bg_color))] ring-[color-mix(in_srgb,var(--tgui--link_color)_38%,transparent)]'
                    : 'bg-[color-mix(in_srgb,var(--tgui--hint_color)_06%,var(--tgui--secondary_bg_color))] ring-[color-mix(in_srgb,var(--tgui--divider_color)_42%,transparent)]'
                }`
        }
        title={titleTip}
      >
        <span
          className={
            compact && pillTight
              ? 'relative flex size-[26px] shrink-0 overflow-hidden rounded-full'
              : compact
                ? 'relative flex size-[30px] shrink-0 overflow-hidden rounded-full'
                : 'flex shrink-0 items-center justify-center rounded-[4px] p-px'
          }
        >
          <ReactionThumb
            src={imageUrl}
            className={compact ? 'size-full object-cover' : 'size-[15px]'}
            roundedClassName={compact ? 'rounded-full' : 'rounded-[4px]'}
          />
        </span>
        <span className={`leading-none text-(--tgui--text_color) ${compact ? 'pr-px' : 'pr-0.5'}`}>{count}</span>
      </button>
      {showBubble ? (
        <div
          role="tooltip"
          className="absolute bottom-full left-1/2 z-[90] mb-2 min-w-[168px] max-w-[226px] -translate-x-1/2 rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-2.5 shadow-[0_8px_32px_rgba(0,0,0,0.22)]"
        >
          <p className="mb-1 text-[10px] font-medium text-(--tgui--hint_color)">Кто реагировал</p>
          {actors === null && actorsErr === null ? (
            <p className="text-[10px] text-(--tgui--hint_color)">Загрузка…</p>
          ) : null}
          {actorsErr !== null ? (
            <p className="text-[10px] text-(--tgui--destructive_text_color)">Не удалось загрузить</p>
          ) : null}
          {actors !== null && actors.length === 0 ? (
            <p className="text-[10px] text-(--tgui--hint_color)">Пока никого</p>
          ) : null}
          {actors !== null && actors.length > 0 ? (
            <ul className="flex max-h-28 flex-wrap gap-2 overflow-y-auto">
              {actors.map((a) => (
                <li key={a.id} title={displayActorName(a)} className="flex flex-col items-center gap-0.5">
                  {a.photo_url ? (
                    <Avatar src={a.photo_url} acronym={displayActorName(a).slice(0, 1)} size={28} />
                  ) : (
                    <Avatar acronym={displayActorName(a).slice(0, 2)} size={28} />
                  )}
                  <span className="line-clamp-1 max-w-[56px] text-center text-[9px] text-(--tgui--hint_color)">
                    {displayActorName(a)}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
