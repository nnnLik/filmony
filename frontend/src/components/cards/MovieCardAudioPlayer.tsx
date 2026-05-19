import { IconButton } from '@telegram-apps/telegram-ui'
import { Pause, Play } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

import { MOVIE_CARD_AUDIO_PLAY_START_DELAY_MS, movieCardAudioSrc } from '../../lib/movieCardAudioMedia'

type MovieCardAudioPlayerProps = {
  audioUrl: string
}

export function MovieCardAudioPlayer({ audioUrl }: MovieCardAudioPlayerProps) {
  const src = movieCardAudioSrc(audioUrl)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [paused, setPaused] = useState(true)

  useEffect(() => {
    const el = audioRef.current
    if (el == null) return
    const onPlay = () => setPaused(false)
    const onPause = () => setPaused(true)
    el.addEventListener('play', onPlay)
    el.addEventListener('pause', onPause)
    return () => {
      el.removeEventListener('play', onPlay)
      el.removeEventListener('pause', onPause)
    }
  }, [src])

  const toggle = useCallback(() => {
    const el = audioRef.current
    if (el == null) return
    if (el.paused) {
      void (async () => {
        await new Promise<void>((resolve) => {
          window.setTimeout(resolve, MOVIE_CARD_AUDIO_PLAY_START_DELAY_MS)
        })
        el.muted = false
        void el.play().catch(() => {
          // ignore — user can tap again
        })
      })()
    } else {
      el.pause()
    }
  }, [])

  if (typeof document === 'undefined') {
    return null
  }

  return createPortal(
    <div className="pointer-events-none fixed inset-x-0 bottom-0 z-100 flex justify-end p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
      <div className="pointer-events-auto shadow-[0_8px_28px_rgba(0,0,0,0.35)]">
        <IconButton
          type="button"
          size="l"
          mode="bezeled"
          className="rounded-full!"
          aria-label={paused ? 'Воспроизвести' : 'Пауза'}
          onClick={() => void toggle()}
        >
          {paused ? (
            <Play className="relative z-1 block size-[22px]" strokeWidth={1.75} aria-hidden />
          ) : (
            <Pause className="relative z-1 block size-[22px]" strokeWidth={1.75} aria-hidden />
          )}
        </IconButton>
      </div>
      <audio key={src} ref={audioRef} src={src} preload="metadata" playsInline className="hidden" />
    </div>,
    document.body,
  )
}
