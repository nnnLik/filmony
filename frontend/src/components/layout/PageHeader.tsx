import { useEffect, useRef, type ReactNode } from 'react'

import { useHeaderPepeGifSrc } from '../../lib/pepeGif'

type PageHeaderProps = {
  title: string
  showPepe?: boolean
  pepeClassName?: string
  actions?: ReactNode
  tabs?: ReactNode
  subtitle?: ReactNode
  className?: string
}

export function PageHeader({
  title,
  showPepe = true,
  pepeClassName,
  actions,
  tabs,
  subtitle,
  className,
}: PageHeaderProps) {
  const headerPepeSrc = useHeaderPepeGifSrc()
  const headerRef = useRef<HTMLElement | null>(null)

  // Publishes the real header height so sticky sub-navigation can align right below it.
  useEffect(() => {
    const node = headerRef.current
    if (node == null) {
      return
    }
    const publish = () => {
      document.documentElement.style.setProperty(
        '--filmony-page-header-h',
        `${Math.round(node.getBoundingClientRect().height)}px`,
      )
    }
    publish()
    if (typeof ResizeObserver === 'undefined') {
      return
    }
    const observer = new ResizeObserver(publish)
    observer.observe(node)
    return () => {
      observer.disconnect()
    }
  }, [])

  return (
    <header
      ref={headerRef}
      className={`sticky top-0 z-20 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] backdrop-blur-md ${className ?? ''}`}
    >
      <div className="px-4 pb-3 pt-3">
        <div className={`flex items-center gap-2 ${tabs != null || subtitle != null ? 'mb-3' : ''}`}>
          <div className="flex min-w-0 flex-1 items-center gap-1.5">
            <h1 className="min-w-0 shrink truncate bg-linear-to-r from-(--filmony-mint,#5eead4) via-(--filmony-text,#e8f0f7) to-(--filmony-amber,#e8b86d) bg-clip-text text-lg font-semibold tracking-tight text-transparent">
              {title}
            </h1>
            {showPepe ? (
              <img
                className={pepeClassName}
                src={headerPepeSrc}
                alt=""
                width={28}
                height={28}
                decoding="async"
                aria-hidden
              />
            ) : null}
          </div>
          {actions != null ? (
            <div className="flex shrink-0 items-center gap-1">{actions}</div>
          ) : null}
        </div>
        {tabs}
        {subtitle}
      </div>
    </header>
  )
}
