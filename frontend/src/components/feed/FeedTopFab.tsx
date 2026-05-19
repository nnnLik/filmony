import { IconButton } from '@telegram-apps/telegram-ui'
import { ChevronUp, RefreshCw, Volume2, VolumeX } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'

import { useOptionalFeedCardGlobalAudio } from '../../hooks/useFeedCardGlobalAudio'

const SCROLL_SHOW_AFTER_PX = 240
const SCROLL_NEAR_TOP_PX = 12

function readScrollY(): number {
  return window.scrollY || document.documentElement.scrollTop || 0
}

export type FeedTopFabProps = {
  /** Максимальная версия головы из SSE (или начальное значение с API). */
  liveHeadVersion: number
  /** Версия, подтверждённая последним успешным fetch ленты. */
  ackHeadVersion: number
  onRefetch: () => Promise<void>
}

/**
 * FAB только для главной ленты: «наверх» при скролле вниз; наверху при live > ack — круглое «обновить»;
 * красная точка на стрелке, пока не у верха. После плавного скролла наверх флаг не гасим по пути.
 */
export function FeedTopFab({ liveHeadVersion, ackHeadVersion, onRefetch }: FeedTopFabProps) {
  const feedAudio = useOptionalFeedCardGlobalAudio()
  const [scrollY, setScrollY] = useState(0)
  const [reloadArmed, setReloadArmed] = useState(false)
  const [refetchBusy, setRefetchBusy] = useState(false)
  /** Пока едет smooth scroll «наверх», не сбрасывать reloadArmed (иначе первый же тик с y>160 гасит флаг). */
  const scrollToTopInProgressRef = useRef(false)

  useEffect(() => {
    const onScroll = () => {
      const y = readScrollY()
      setScrollY(y)
      if (scrollToTopInProgressRef.current) {
        if (y <= SCROLL_NEAR_TOP_PX) {
          scrollToTopInProgressRef.current = false
        }
        return
      }
      setReloadArmed((armed) => (armed && y > 160 ? false : armed))
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const hasPendingNew = liveHeadVersion > ackHeadVersion
  const atTop = scrollY <= SCROLL_NEAR_TOP_PX
  const showFab = scrollY > SCROLL_SHOW_AFTER_PX || reloadArmed || (atTop && hasPendingNew)
  const hasNewDot = hasPendingNew && scrollY > 120 && !atTop
  const showReload = atTop && (reloadArmed || hasPendingNew)

  const goTop = useCallback(() => {
    scrollToTopInProgressRef.current = true
    const el = document.scrollingElement ?? document.documentElement
    const reduce =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    el.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' })
    setReloadArmed(true)
    window.setTimeout(() => {
      scrollToTopInProgressRef.current = false
    }, 900)
  }, [])

  const doRefetch = useCallback(async () => {
    if (refetchBusy) return
    setRefetchBusy(true)
    try {
      await onRefetch()
    } finally {
      setRefetchBusy(false)
      setReloadArmed(false)
    }
  }, [onRefetch, refetchBusy])

  const onClick = useCallback(() => {
    if (showReload) {
      void doRefetch()
      return
    }
    goTop()
  }, [doRefetch, goTop, showReload])

  const showAudioFab = feedAudio != null

  return (
    <div
      className={`fixed right-3 z-39 flex flex-col items-end gap-2 transition-[opacity,transform] duration-300 ease-out motion-reduce:transition-none ${
        showFab || showAudioFab
          ? 'pointer-events-auto opacity-100 translate-y-0'
          : 'pointer-events-none opacity-0 translate-y-3'
      }`}
      style={{
        bottom: 'calc(5.75rem + env(safe-area-inset-bottom, 0px) + 10px)',
      }}
      aria-hidden={!showFab && !showAudioFab}
    >
      {showAudioFab ? (
        <IconButton
          type="button"
          size="m"
          mode={feedAudio.enabled ? 'bezeled' : 'gray'}
          className="rounded-full border border-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_28%,transparent)] bg-[color-mix(in_srgb,var(--filmony-surface,#111b27)_88%,transparent)] shadow-[0_8px_28px_rgba(0,0,0,.4),inset_0_1px_0_rgba(255,255,255,.05)] backdrop-blur-md"
          style={{ WebkitBackdropFilter: 'blur(12px)' }}
          aria-label={feedAudio.enabled ? 'Выключить звук карточек в ленте' : 'Включить звук карточек в ленте'}
          aria-pressed={feedAudio.enabled}
          title={feedAudio.enabled ? 'Звук ленты включён' : 'Звук ленты выключен'}
          onClick={feedAudio.toggleFeedAudioEnabled}
        >
          {feedAudio.enabled ? (
            <Volume2 className="relative z-1 block size-[20px]" strokeWidth={2} aria-hidden />
          ) : (
            <VolumeX className="relative z-1 block size-[20px]" strokeWidth={2} aria-hidden />
          )}
        </IconButton>
      ) : null}
      <div
        className={`relative transition-[opacity,transform] duration-300 ease-out motion-reduce:transition-none ${
          showFab ? 'opacity-100' : 'pointer-events-none opacity-0'
        }`}
      >
        {hasNewDot ? (
          <span
            className="absolute -right-0.5 -top-0.5 z-2 size-2.5 rounded-full bg-red-500 ring-2 ring-[color-mix(in_srgb,var(--filmony-surface,#111b27)_92%,transparent)]"
            aria-hidden
          />
        ) : null}
        <IconButton
          type="button"
          size="m"
          mode="gray"
          className="rounded-full border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_22%,transparent)] bg-[color-mix(in_srgb,var(--filmony-surface,#111b27)_88%,transparent)] shadow-[0_8px_28px_rgba(0,0,0,.4),inset_0_1px_0_rgba(255,255,255,.05)] backdrop-blur-md"
          style={{ WebkitBackdropFilter: 'blur(12px)' }}
          aria-label={showReload ? 'Обновить ленту' : 'Наверх'}
          disabled={refetchBusy}
          onClick={onClick}
        >
          {showReload ? (
            <RefreshCw
              className={`relative z-1 block size-[20px] ${refetchBusy ? 'animate-spin' : ''}`}
              strokeWidth={2}
              aria-hidden
            />
          ) : (
            <ChevronUp className="relative z-1 block size-[22px]" strokeWidth={2} aria-hidden />
          )}
        </IconButton>
      </div>
    </div>
  )
}
