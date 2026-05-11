import { Button } from '@telegram-apps/telegram-ui'
import { useMemo, useState } from 'react'

type FilmSynopsisBlockProps = {
  shortDescription?: string | null
  description?: string | null
  className?: string
}

/** Короткий синопсис с Кинопоиска; при необходимости раскрытие полного description. */
export function FilmSynopsisBlock({
  shortDescription,
  description,
  className = '',
}: FilmSynopsisBlockProps) {
  const [expanded, setExpanded] = useState(false)

  const { shortText, fullText, canExpand } = useMemo(() => {
    const s = (shortDescription ?? '').trim()
    const d = (description ?? '').trim()
    if (!s && !d) {
      return { shortText: '', fullText: '', canExpand: false }
    }
    if (!d || d === s) {
      return { shortText: s || d, fullText: d, canExpand: false }
    }
    if (!s) {
      return { shortText: d, fullText: d, canExpand: true }
    }
    return { shortText: s, fullText: d, canExpand: true }
  }, [shortDescription, description])

  if (!shortText && !fullText) {
    return null
  }

  const showToggle = canExpand && !expanded
  const showCollapse = canExpand && expanded

  return (
    <div className={`space-y-1.5 ${className}`.trim()}>
      <p
        className={
          expanded
            ? 'whitespace-pre-wrap text-sm leading-relaxed text-(--tgui--hint_color)'
            : 'line-clamp-4 text-sm leading-relaxed text-(--tgui--hint_color)'
        }
      >
        {expanded && fullText ? fullText : shortText}
      </p>
      {showToggle ? (
        <Button
          type="button"
          size="s"
          mode="plain"
          className="!-ms-1 !min-h-8 !justify-start !px-1 !text-xs font-semibold"
          onClick={() => setExpanded(true)}
        >
          Ещё
        </Button>
      ) : null}
      {showCollapse ? (
        <Button
          type="button"
          size="s"
          mode="plain"
          className="!-ms-1 !min-h-8 !justify-start !px-1 !text-xs font-semibold"
          onClick={() => setExpanded(false)}
        >
          Свернуть
        </Button>
      ) : null}
    </div>
  )
}
