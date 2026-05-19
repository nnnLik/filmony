import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'

import { movieCardAudioSrc } from '../lib/movieCardAudioMedia'

import {
  FeedCardGlobalAudioContext,
  type FeedCardGlobalAudioContextValue,
} from './feedCardGlobalAudioContext'

const STORAGE_KEY = 'filmony-feed-card-audio-enabled'

function readEnabled(): boolean {
  if (typeof window === 'undefined') return true
  try {
    const v = window.localStorage.getItem(STORAGE_KEY)
    if (v == null) return true
    return v === '1' || v === 'true'
  } catch {
    return true
  }
}

function writeEnabled(enabled: boolean): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, enabled ? '1' : '0')
  } catch {
    /* ignore */
  }
}

export function FeedCardGlobalAudioProvider({ children }: { children: ReactNode }) {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [enabled, setEnabled] = useState(readEnabled)
  const [playingCardId, setPlayingCardId] = useState<number | null>(null)
  const [paused, setPaused] = useState(true)

  const setFeedAudioEnabled = useCallback((next: boolean) => {
    setEnabled(next)
    writeEnabled(next)
    if (!next) {
      const el = audioRef.current
      el?.pause()
      setPlayingCardId(null)
      setPaused(true)
    }
  }, [])

  const toggleFeedAudioEnabled = useCallback(() => {
    setFeedAudioEnabled(!enabled)
  }, [enabled, setFeedAudioEnabled])

  const toggleCardAudio = useCallback(
    (cardId: number, audioUrlRaw: string) => {
      const url = audioUrlRaw.trim()
      if (url === '') return

      if (!enabled) {
        setFeedAudioEnabled(true)
      }

      const el = audioRef.current
      if (el == null) return

      const resolvedSrc = movieCardAudioSrc(url)

      if (playingCardId === cardId) {
        if (el.paused) {
          void el.play().catch(() => {})
        } else {
          el.pause()
        }
        return
      }

      setPlayingCardId(cardId)
      el.src = resolvedSrc
      void el.load()
      void el.play().catch(() => {})
    },
    [enabled, playingCardId, setFeedAudioEnabled],
  )

  useEffect(() => {
    const el = audioRef.current
    if (el == null) return

    const sync = () => {
      setPaused(el.paused)
    }

    el.addEventListener('play', sync)
    el.addEventListener('pause', sync)
    el.addEventListener('ended', sync)

    sync()

    return () => {
      el.removeEventListener('play', sync)
      el.removeEventListener('pause', sync)
      el.removeEventListener('ended', sync)
    }
  }, [])

  useEffect(() => {
    const el = audioRef.current
    return () => {
      el?.pause()
    }
  }, [])

  useEffect(() => {
    const onVisibilityChange = () => {
      if (document.visibilityState !== 'visible') {
        audioRef.current?.pause()
      }
    }

    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [])

  const value = useMemo<FeedCardGlobalAudioContextValue>(
    () => ({
      enabled,
      setFeedAudioEnabled,
      toggleFeedAudioEnabled,
      playingCardId,
      paused,
      audioRef,
      toggleCardAudio,
    }),
    [enabled, setFeedAudioEnabled, toggleFeedAudioEnabled, playingCardId, paused, toggleCardAudio],
  )

  return (
    <FeedCardGlobalAudioContext.Provider value={value}>
      {children}
      <audio
        ref={audioRef}
        preload="metadata"
        playsInline
        crossOrigin="anonymous"
        className="hidden"
        aria-hidden
      />
    </FeedCardGlobalAudioContext.Provider>
  )
}
