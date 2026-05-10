import { Avatar } from '@telegram-apps/telegram-ui'
import { useCallback, useEffect, useRef, useState, type CSSProperties, type MouseEvent } from 'react'
import { createPortal } from 'react-dom'
import { Link } from 'react-router-dom'

import type { ReactionActor } from '../../../api/profileTypes'
import { displayActorName } from './displayActorName'
import { ReactionThumb } from './ReactionThumb'

/** TGUI variables are on `AppRoot` inside `#root`; portaling to `document.body` leaves them unset → transparent tooltip. */
function reactionActorsTooltipContainer(): HTMLElement {
  const insideThemedTree = document.getElementById('root')?.firstElementChild
  return insideThemedTree instanceof HTMLElement ? insideThemedTree : document.body
}

export type CountPillProps = {
  disabled: boolean
  mine: boolean
  imageUrl: string
  count: number
  reactors: ReactionActor[]
  onPick: () => void
  compact: boolean
  pillTight?: boolean
}

export function CountPill({
  disabled,
  mine,
  imageUrl,
  count,
  reactors,
  onPick,
  compact,
  pillTight = false,
}: CountPillProps) {
  const anchorRef = useRef<HTMLDivElement>(null)
  const leaveTimerRef = useRef<number | null>(null)
  const [tipOpen, setTipOpen] = useState(false)
  const [tipStyle, setTipStyle] = useState<CSSProperties | null>(null)

  const cancelScheduledClose = useCallback(() => {
    if (leaveTimerRef.current != null) {
      window.clearTimeout(leaveTimerRef.current)
      leaveTimerRef.current = null
    }
  }, [])

  const placeTip = useCallback(() => {
    const el = anchorRef.current
    if (el == null) return
    const r = el.getBoundingClientRect()
    setTipStyle({
      position: 'fixed',
      left: r.left + r.width / 2,
      top: r.top - 6,
      transform: 'translate(-50%, -100%)',
      zIndex: 12_000,
      // Непрозрачный слой: переменные темы + запас на случай сбоя наследования
      backgroundColor: 'var(--tgui--secondary_bg_color, #232323)',
      color: 'var(--tgui--text_color, #eaeaea)',
    })
  }, [])

  const openTip = useCallback(() => {
    cancelScheduledClose()
    placeTip()
    setTipOpen(true)
  }, [placeTip, cancelScheduledClose])

  const closeTip = useCallback(() => {
    setTipOpen(false)
    setTipStyle(null)
  }, [])

  const scheduleClose = useCallback(() => {
    cancelScheduledClose()
    leaveTimerRef.current = window.setTimeout(() => {
      closeTip()
      leaveTimerRef.current = null
    }, 160)
  }, [cancelScheduledClose, closeTip])

  useEffect(() => {
    if (!tipOpen) return
    const onScrollOrResize = () => placeTip()
    window.addEventListener('scroll', onScrollOrResize, true)
    window.addEventListener('resize', onScrollOrResize)
    return () => {
      window.removeEventListener('scroll', onScrollOrResize, true)
      window.removeEventListener('resize', onScrollOrResize)
    }
  }, [tipOpen, placeTip])

  useEffect(() => () => cancelScheduledClose(), [cancelScheduledClose])

  const showTip = tipOpen && tipStyle != null
  const moreHidden = count > reactors.length

  const tipPortal =
    showTip &&
    typeof document !== 'undefined' &&
    createPortal(
      <div
        role="tooltip"
        style={tipStyle}
        className="pointer-events-auto min-w-[168px] max-w-[240px] rounded-2xl border border-(--tgui--divider_color) p-2.5 shadow-[0_8px_32px_rgba(0,0,0,0.45)]"
        onMouseEnter={cancelScheduledClose}
        onMouseLeave={scheduleClose}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <p className="mb-1 text-[10px] font-medium text-(--tgui--hint_color)">Кто реагировал</p>
        {reactors.length === 0 ? (
          <p className="text-[10px] text-(--tgui--hint_color)">Нет данных</p>
        ) : (
          <ul className="flex max-h-32 flex-wrap gap-2 overflow-y-auto">
            {reactors.map((a) => {
              const label = displayActorName(a)
              const stopBubbling = (e: MouseEvent) => {
                e.stopPropagation()
              }
              return (
                <li key={a.id} className="flex flex-col items-center gap-0.5">
                  <Link
                    to={`/u/${encodeURIComponent(a.id)}`}
                    title={label}
                    aria-label={`Профиль: ${label}`}
                    className="flex flex-col items-center gap-0.5 no-underline outline-none ring-(--tgui--link_color) focus-visible:rounded-lg focus-visible:ring-2"
                    onMouseDown={stopBubbling}
                    onClick={stopBubbling}
                  >
                    {a.photo_url ? (
                      <Avatar src={a.photo_url} acronym={label.slice(0, 1)} size={28} />
                    ) : (
                      <Avatar acronym={label.slice(0, 2)} size={28} />
                    )}
                    <span className="line-clamp-1 max-w-[56px] text-center text-[9px] text-(--tgui--hint_color)">
                      {label}
                    </span>
                  </Link>
                </li>
              )
            })}
          </ul>
        )}
        {moreHidden ? (
          <p className="mt-1.5 text-[9px] text-(--tgui--hint_color)">
            И ещё {count - reactors.length}…
          </p>
        ) : null}
      </div>,
      reactionActorsTooltipContainer(),
    )

  return (
    <>
      <div
        ref={anchorRef}
        className="relative shrink-0"
        onMouseEnter={openTip}
        onMouseLeave={scheduleClose}
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
          aria-label="Реакция: нажмите, чтобы поставить или убрать; наведите курсор, чтобы увидеть, кто отреагировал"
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
          <span className={`leading-none text-(--tgui--text_color) ${compact ? 'pr-px' : 'pr-0.5'}`}>
            {count}
          </span>
        </button>
      </div>
      {tipPortal}
    </>
  )
}
