import type { ReactNode } from 'react'
import { Link } from 'react-router'

export type PosterTileProps = {
  posterUrl: string | null
  title: string
  href?: string | null
  ariaLabel?: string
  overlay?: ReactNode
  footer?: ReactNode
  shellClassName?: string
  rounded?: 'lg' | 'xl'
}

const ROUNDED_CLASS = {
  lg: 'rounded-lg',
  xl: 'rounded-xl',
} as const

export function PosterTile({
  posterUrl,
  title,
  href,
  ariaLabel,
  overlay,
  footer,
  shellClassName = '',
  rounded = 'xl',
}: PosterTileProps) {
  const roundedClass = ROUNDED_CLASS[rounded]
  const shellClass = `relative block overflow-hidden ${roundedClass} border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) ${shellClassName}`.trim()

  const posterInner = (
    <div className={`relative aspect-2/3 w-full ${footer == null ? '' : ''}`}>
      {posterUrl ? (
        <img src={posterUrl} alt={title} className="h-full w-full object-cover" />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-[11px] text-(--tgui--hint_color)">
          Нет постера
        </div>
      )}
      {overlay}
    </div>
  )

  const content = (
    <>
      {posterInner}
      {footer}
    </>
  )

  if (href != null && href !== '') {
    return (
      <Link
        to={href}
        className={`${shellClass} no-underline`}
        aria-label={ariaLabel ?? `Открыть «${title}»`}
      >
        {content}
      </Link>
    )
  }

  return (
    <div className={shellClass} aria-label={ariaLabel}>
      {content}
    </div>
  )
}
