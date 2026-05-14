import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'

import { BottomNav } from '../components/navigation/BottomNav'
import { ensurePepeDancingGifPreloaded, PEPE_DANCING_GIF_URL } from '../lib/pepeGif'

import './AppShell.css'

const DESKTOP_SIDE_COPY = 'ЗДЕСЬ МОГЛА БЫ БЫТЬ ВАША РЕКЛАМА'

export function AppShell() {
  useEffect(() => {
    void ensurePepeDancingGifPreloaded()
  }, [])

  return (
    <div className="app-shell flex min-h-dvh flex-col bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <div className="app-shell__body">
        <aside className="app-shell__side app-shell__side--left" aria-hidden="true">
          <div className="app-shell__side-stack">
            <img
              className="app-shell__side-ad-gif"
              src={PEPE_DANCING_GIF_URL}
              alt=""
              loading="lazy"
              decoding="async"
              width={112}
              height={112}
            />
            <p className="app-shell__side-text">{DESKTOP_SIDE_COPY}</p>
          </div>
        </aside>
        <div className="app-shell__main mx-auto w-full max-w-md flex-1 pb-[calc(5.75rem+env(safe-area-inset-bottom))]">
          <Outlet />
        </div>
        <aside className="app-shell__side app-shell__side--right" aria-hidden="true">
          <div className="app-shell__side-stack">
            <img
              className="app-shell__side-ad-gif"
              src={PEPE_DANCING_GIF_URL}
              alt=""
              loading="lazy"
              decoding="async"
              width={112}
              height={112}
            />
            <p className="app-shell__side-text">{DESKTOP_SIDE_COPY}</p>
          </div>
        </aside>
      </div>
      <BottomNav />
    </div>
  )
}
