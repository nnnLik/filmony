import { useCallback, useEffect, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import { Outlet } from 'react-router-dom'

import { BottomNav } from '../components/navigation/BottomNav'
import {
  PEPE_DANCING_GIF_URL,
  SIDE_DISCO_RAIN_GIF_URL,
  prewarmAllPepeDiscoAssets,
  toggleHeaderPepeGifAfterDiscoCompletes,
} from '../lib/pepeGif'

import './AppShell.css'

const DESKTOP_SIDE_COPY = 'ЗДЕСЬ МОГЛА БЫ БЫТЬ ВАША РЕКЛАМА'
const SIDE_PEPE_CLICKS_FOR_DISCO = 5
const DISCO_BORDER_MS = 9000

/** Fixed cap: sprites per gutter, mounted only during the disco window (×2 gutters). */
const DISCO_RAIN_SPRITES_PER_SIDE = 50

type DiscoRainSpriteConfig = Readonly<{
  sizePx: number
  /** Precomputed once at module load — avoids new style object allocations each disco render. */
  imgStyle: CSSProperties
}>

function buildDiscoRainSideSprites(sideIndex: 0 | 1): readonly DiscoRainSpriteConfig[] {
  const sprites: DiscoRainSpriteConfig[] = []
  for (let i = 0; i < DISCO_RAIN_SPRITES_PER_SIDE; i += 1) {
    const leftPct = 6 + (((i * 37 + sideIndex * 19) % 79) / 100) * 88
    const delayMs = (i * 68 + sideIndex * 47) % 2400
    const driftPx = -44 + (((i * 23 + sideIndex * 31) % 89) / 88) * 88
    const durationMs = 1750 + (i % 11) * 95
    const sizePx = 26 + ((i * 3 + sideIndex * 7) % 6) * 6
    const rotateDeg = -14 + (((i + sideIndex) * 13) % 29)
    sprites.push({
      sizePx,
      imgStyle: {
        '--rain-left-pct': `${leftPct}%`,
        '--rain-delay': `${delayMs}ms`,
        '--rain-dur': `${durationMs}ms`,
        '--rain-drift-end': `${driftPx}px`,
        '--rain-rotate': `${rotateDeg}deg`,
        width: sizePx,
        height: 'auto',
      } as CSSProperties,
    })
  }
  return sprites
}

const DISCO_RAIN_LEFT_SPRITES = buildDiscoRainSideSprites(0)
const DISCO_RAIN_RIGHT_SPRITES = buildDiscoRainSideSprites(1)

export function AppShell() {
  const [discoSides, setDiscoSides] = useState(false)
  /** True while side disco visuals are active; kept in sync in the click handler and disco timeout only (never during render — eslint `react-hooks/refs`). */
  const discoSidesRef = useRef(false)
  const discoOffTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pepeClickCountRef = useRef(0)

  useEffect(() => {
    void prewarmAllPepeDiscoAssets()
  }, [])

  useEffect(() => {
    return () => {
      if (discoOffTimeoutRef.current !== null) {
        clearTimeout(discoOffTimeoutRef.current)
      }
    }
  }, [])

  const handleSidePepeClick = useCallback(() => {
    pepeClickCountRef.current += 1
    if (pepeClickCountRef.current < SIDE_PEPE_CLICKS_FOR_DISCO) {
      return
    }
    pepeClickCountRef.current = 0
    if (discoOffTimeoutRef.current !== null) {
      clearTimeout(discoOffTimeoutRef.current)
    }
    const extendingExistingSession = discoSidesRef.current
    if (!extendingExistingSession) {
      toggleHeaderPepeGifAfterDiscoCompletes()
    }
    discoSidesRef.current = true
    setDiscoSides(true)
    discoOffTimeoutRef.current = setTimeout(() => {
      discoSidesRef.current = false
      setDiscoSides(false)
      discoOffTimeoutRef.current = null
    }, DISCO_BORDER_MS)
  }, [])

  const sideClassLeft = [
    'app-shell__side',
    'app-shell__side--left',
    discoSides ? 'app-shell__side--disco' : '',
  ]
    .filter(Boolean)
    .join(' ')
  const sideClassRight = [
    'app-shell__side',
    'app-shell__side--right',
    discoSides ? 'app-shell__side--disco' : '',
  ]
    .filter(Boolean)
    .join(' ')

  const shellClassName = ['app-shell', 'flex min-h-dvh flex-col bg-(--tgui--bg_color) text-(--tgui--text_color)']
    .concat(discoSides ? ['app-shell--side-disco'] : [])
    .join(' ')

  return (
    <div className={shellClassName}>
      <img
        className="app-shell__disco-rain-decode-warm"
        src={SIDE_DISCO_RAIN_GIF_URL}
        alt=""
        aria-hidden
        decoding="async"
        width={1}
        height={1}
        draggable={false}
      />
      <div className="app-shell__body">
        <aside className={sideClassLeft}>
          <div className="app-shell__side-stack">
            <button
              type="button"
              className="app-shell__side-pepe-trigger"
              onClick={handleSidePepeClick}
              aria-label="Декоративная анимация"
            >
              <img
                className="app-shell__side-ad-gif"
                src={PEPE_DANCING_GIF_URL}
                alt=""
                loading="lazy"
                decoding="async"
                width={112}
                height={112}
                draggable={false}
              />
            </button>
            <p className="app-shell__side-text">{DESKTOP_SIDE_COPY}</p>
          </div>
        </aside>
        <div
          className={[
            'app-shell__main mx-auto w-full max-w-md flex-1 pb-[calc(5.75rem+env(safe-area-inset-bottom))]',
            discoSides ? 'app-shell__main--disco' : '',
          ]
            .filter(Boolean)
            .join(' ')}
        >
          <Outlet />
        </div>
        <aside className={sideClassRight}>
          <div className="app-shell__side-stack">
            <button
              type="button"
              className="app-shell__side-pepe-trigger"
              onClick={handleSidePepeClick}
              aria-label="Декоративная анимация"
            >
              <img
                className="app-shell__side-ad-gif"
                src={PEPE_DANCING_GIF_URL}
                alt=""
                loading="lazy"
                decoding="async"
                width={112}
                height={112}
                draggable={false}
              />
            </button>
            <p className="app-shell__side-text">{DESKTOP_SIDE_COPY}</p>
          </div>
        </aside>
        {discoSides ? (
          <>
            <div className="app-shell__disco-rain app-shell__disco-rain--left" aria-hidden>
              {DISCO_RAIN_LEFT_SPRITES.map((cfg, idx) => (
                <img
                  key={`disco-rain-l-${idx}`}
                  className="app-shell__disco-rain-sprite"
                  src={SIDE_DISCO_RAIN_GIF_URL}
                  alt=""
                  decoding="async"
                  draggable={false}
                  width={cfg.sizePx}
                  height={cfg.sizePx}
                  style={cfg.imgStyle}
                />
              ))}
            </div>
            <div className="app-shell__disco-rain app-shell__disco-rain--right" aria-hidden>
              {DISCO_RAIN_RIGHT_SPRITES.map((cfg, idx) => (
                <img
                  key={`disco-rain-r-${idx}`}
                  className="app-shell__disco-rain-sprite"
                  src={SIDE_DISCO_RAIN_GIF_URL}
                  alt=""
                  decoding="async"
                  draggable={false}
                  width={cfg.sizePx}
                  height={cfg.sizePx}
                  style={cfg.imgStyle}
                />
              ))}
            </div>
          </>
        ) : null}
      </div>
      <BottomNav />
    </div>
  )
}
