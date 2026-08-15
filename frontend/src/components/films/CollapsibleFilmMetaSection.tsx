import { ChevronDown } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { FILM_CATALOG_TEXT_SIZE, type FilmCatalogMetadataSize } from '../../lib/filmCatalogMetadataDisplay'

export type CollapsibleFilmMetaSectionProps = {
  title: string
  summary: string
  size?: FilmCatalogMetadataSize
  children: ReactNode
}

export function CollapsibleFilmMetaSection({
  title,
  summary,
  size = 'md',
  children,
}: CollapsibleFilmMetaSectionProps) {
  const [open, setOpen] = useState(false)

  return (
    <div>
      <button
        type="button"
        className={`flex w-full items-center gap-1.5 text-left ${FILM_CATALOG_TEXT_SIZE[size]} text-(--tgui--hint_color) transition active:opacity-80`}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <ChevronDown
          className={`size-3.5 shrink-0 text-(--tgui--hint_color) transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden
        />
        <span className="font-semibold text-(--tgui--text_color)">{title}</span>
        {!open ? <span className="min-w-0 truncate opacity-80">{summary}</span> : null}
      </button>
      {open ? <div className="mt-1.5">{children}</div> : null}
    </div>
  )
}
