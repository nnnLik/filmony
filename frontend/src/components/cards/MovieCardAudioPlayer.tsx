import { IconButton } from '@telegram-apps/telegram-ui'
import { Download, Pause, Play } from 'lucide-react'
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'

import { ApiError } from '../../api/client'
import { postSendUserCardAudioToTelegram } from '../../api/cardApi'
import { movieCardAudioSrc } from '../../lib/movieCardAudioMedia'
import { safeHapticSuccess } from '../../lib/safeHaptic'
import {
  isTelegramChatUnavailableDetail,
  notificationFailureMessage,
} from '../../lib/telegramNotificationError'

type MovieCardAudioPlayerProps = {
  cardId: number
  audioUrl: string
  /** Для визуализации на постере: передаётся смонтированный `<audio>`. */
  onAttachedAudioElement?: (element: HTMLAudioElement | null) => void
  /**
   * Лента: один общий `<audio>` в `FeedCardGlobalAudioProvider` — локальный тег не монтируем.
   */
  feedGlobal?: {
    paused: boolean
    onToggle: () => void
  }
  /**
   * `compact` — один ряд поменьше для оверлея на постере (play заметнее, download вторичнее).
   */
  variant?: 'default' | 'compact'
  className?: string
}

export function MovieCardAudioPlayer({
  cardId,
  audioUrl,
  onAttachedAudioElement,
  feedGlobal,
  variant = 'default',
  className,
}: MovieCardAudioPlayerProps) {
  const src = movieCardAudioSrc(audioUrl)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const usesFeedGlobal = feedGlobal != null

  useLayoutEffect(() => {
    if (usesFeedGlobal) {
      return
    }
    onAttachedAudioElement?.(audioRef.current)
    return () => {
      onAttachedAudioElement?.(null)
    }
  }, [usesFeedGlobal, src, onAttachedAudioElement])
  const [localPaused, setLocalPaused] = useState(true)
  const paused = usesFeedGlobal ? feedGlobal.paused : localPaused
  const [downloadBusy, setDownloadBusy] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)
  const [telegramOk, setTelegramOk] = useState<string | null>(null)

  useEffect(() => {
    if (usesFeedGlobal) {
      return
    }
    const el = audioRef.current
    if (el == null) return
    const onPlay = () => setLocalPaused(false)
    const onPause = () => setLocalPaused(true)
    el.addEventListener('play', onPlay)
    el.addEventListener('pause', onPause)
    return () => {
      el.removeEventListener('play', onPlay)
      el.removeEventListener('pause', onPause)
    }
  }, [src, usesFeedGlobal])

  useEffect(() => {
    if (telegramOk == null) return
    const t = window.setTimeout(() => {
      setTelegramOk(null)
    }, 6000)
    return () => {
      window.clearTimeout(t)
    }
  }, [telegramOk])

  const toggle = useCallback(() => {
    setDownloadError(null)
    setTelegramOk(null)
    if (usesFeedGlobal) {
      feedGlobal.onToggle()
      return
    }
    const el = audioRef.current
    if (el == null) return
    if (el.paused) {
      el.muted = false
      void el.play().catch(() => {
        /* autoplay / gesture policies — пользователь может нажать ещё раз */
      })
    } else {
      el.pause()
    }
  }, [feedGlobal, usesFeedGlobal])

  const onSendToTelegram = useCallback(async () => {
    setDownloadError(null)
    setTelegramOk(null)
    setDownloadBusy(true)
    try {
      await postSendUserCardAudioToTelegram(cardId)
      setTelegramOk('Аудио отправлено в Telegram — откройте чат с ботом Filmony.')
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) {
        if (isTelegramChatUnavailableDetail(e.detail)) {
          setDownloadError(e.detail.message)
        } else {
          setDownloadError(notificationFailureMessage(e.detail))
        }
      } else {
        setDownloadError(e instanceof Error ? e.message : 'Не удалось отправить')
      }
    } finally {
      setDownloadBusy(false)
    }
  }, [cardId])

  const isCompact = variant === 'compact'

  return (
    <div
      className={
        isCompact
          ? `flex min-w-0 flex-col gap-0.5 ${className ?? ''}`.trim()
          : `flex flex-col gap-2 ${className ?? ''}`.trim()
      }
    >
      <div className={`flex flex-nowrap items-center ${isCompact ? 'gap-2' : 'flex-wrap gap-2'}`}>
        <IconButton
          type="button"
          size={isCompact ? 'm' : 'l'}
          mode="bezeled"
          className={
            isCompact
              ? 'rounded-full! ring-1 ring-white/40 shadow-[0_3px_14px_rgba(0,0,0,0.45)]'
              : 'rounded-full!'
          }
          aria-label={paused ? 'Воспроизвести' : 'Пауза'}
          onClick={() => void toggle()}
        >
          {paused ? (
            <Play
              className={`relative z-1 block ${isCompact ? 'size-[19px]' : 'size-[22px]'}`}
              strokeWidth={isCompact ? 2 : 1.75}
              aria-hidden
            />
          ) : (
            <Pause
              className={`relative z-1 block ${isCompact ? 'size-[19px]' : 'size-[22px]'}`}
              strokeWidth={isCompact ? 2 : 1.75}
              aria-hidden
            />
          )}
        </IconButton>
        <IconButton
          type="button"
          size={isCompact ? 's' : 'l'}
          mode="gray"
          className={
            isCompact
              ? 'rounded-full! ring-1 ring-white/22 bg-[color-mix(in_srgb,#fff_10%,transparent)] opacity-95 motion-safe:hover:opacity-100'
              : 'rounded-full! opacity-88 motion-safe:hover:opacity-100'
          }
          aria-label="Отправить аудио в Telegram"
          disabled={downloadBusy}
          onClick={() => void onSendToTelegram()}
        >
          <Download
            className={`relative z-1 block ${isCompact ? 'size-[17px]' : 'size-[22px]'}`}
            strokeWidth={isCompact ? 2 : 1.75}
            aria-hidden
          />
        </IconButton>
        {usesFeedGlobal ? null : (
          <audio
            key={src}
            ref={audioRef}
            src={src}
            preload="metadata"
            playsInline
            crossOrigin="anonymous"
            className="hidden"
          />
        )}
      </div>
      {telegramOk != null ? (
        <p
          className={
            isCompact
              ? 'max-w-46 truncate text-center text-[10px] leading-tight text-white/84'
              : 'text-xs text-(--tgui--hint_color)'
          }
          title={telegramOk}
        >
          {telegramOk}
        </p>
      ) : null}
      {downloadError != null ? (
        <p
          className={
            isCompact
              ? 'max-w-46 truncate text-center text-[10px] leading-tight text-rose-300'
              : 'text-xs text-(--tgui--destructive_text_color)'
          }
          title={downloadError}
        >
          {downloadError}
        </p>
      ) : null}
    </div>
  )
}
