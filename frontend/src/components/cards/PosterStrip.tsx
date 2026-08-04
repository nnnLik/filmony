import type { ReactNode } from 'react'

export type PosterStripProps = {
  title?: string
  children: ReactNode
  className?: string
}

export function PosterStrip({ title, children, className = '' }: PosterStripProps) {
  return (
    <section
      className={`border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_55%,transparent)] px-4 py-2 ${className}`.trim()}
    >
      {title != null && title !== '' ? (
        <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-(--tgui--hint_color)">
          {title}
        </p>
      ) : null}
      <div className="flex gap-3 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {children}
      </div>
    </section>
  )
}
