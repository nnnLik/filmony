import { IconButton } from '@telegram-apps/telegram-ui'
import { ChevronUp } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'

const SCROLL_SHOW_AFTER_PX = 240

function pathHasBottomNav(pathname: string): boolean {
  if (pathname === '/') return true
  if (pathname.startsWith('/profile')) return true
  if (pathname === '/cards/new') return true
  return false
}

function readScrollY(): number {
  return window.scrollY || document.documentElement.scrollTop || 0
}

export function ScrollToTopFab() {
  const { pathname } = useLocation()
  const isFeedRoot = pathname === '/'
  const aboveBottomNav = pathHasBottomNav(pathname)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (isFeedRoot) {
      setVisible(false)
      return
    }
    const onScroll = () => {
      setVisible(readScrollY() > SCROLL_SHOW_AFTER_PX)
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [pathname, isFeedRoot])

  const goTop = useCallback(() => {
    const el = document.scrollingElement ?? document.documentElement
    const reduce =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    el.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' })
  }, [])

  if (isFeedRoot) {
    return null
  }

  return (
    <div
      className={`fixed right-3 z-38 transition-[opacity,transform] duration-300 ease-out motion-reduce:transition-none ${
        visible ? 'pointer-events-auto opacity-100 translate-y-0' : 'pointer-events-none opacity-0 translate-y-3'
      }`}
      style={{
        bottom: aboveBottomNav
          ? 'calc(5.75rem + env(safe-area-inset-bottom, 0px) + 10px)'
          : 'calc(0.75rem + env(safe-area-inset-bottom, 0px))',
      }}
      aria-hidden={!visible}
    >
      <IconButton
        type="button"
        size="m"
        mode="gray"
        className="rounded-full border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_22%,transparent)] bg-[color-mix(in_srgb,var(--filmony-surface,#111b27)_88%,transparent)] shadow-[0_8px_28px_rgba(0,0,0,.4),inset_0_1px_0_rgba(255,255,255,.05)] backdrop-blur-md"
        style={{ WebkitBackdropFilter: 'blur(12px)' }}
        aria-label="Наверх"
        onClick={goTop}
      >
        <ChevronUp className="relative z-1 block size-[22px]" strokeWidth={2} aria-hidden />
      </IconButton>
    </div>
  )
}
