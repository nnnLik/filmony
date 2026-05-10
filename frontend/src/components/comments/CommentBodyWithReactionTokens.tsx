import { useEffect, useMemo, useState } from 'react'

import type { ReactionGroupedCatalog } from '../../api/profileTypes'
import { ApiError, formatApiDetail } from '../../api/client'
import { loadReactionCatalog } from '../../lib/reactionCatalogCache'
import { splitCommentTextIntoSegments } from '../../lib/commentReactionTokens'
import { resolveApiMediaUrl } from '../../lib/resolveApiMediaUrl'

type CommentBodyWithReactionTokensProps = {
  text: string
  className?: string
}

function buildImageUrlMap(catalog: ReactionGroupedCatalog): Map<number, string> {
  const m = new Map<number, string>()
  for (const tab of catalog.tabs) {
    for (const it of tab.items) {
      m.set(it.id, it.image_url)
    }
  }
  for (const it of catalog.recent) {
    m.set(it.id, it.image_url)
  }
  return m
}

export function CommentBodyWithReactionTokens({ text, className }: CommentBodyWithReactionTokensProps) {
  const segments = useMemo(() => splitCommentTextIntoSegments(text), [text])
  const needsCatalog = useMemo(() => segments.some((s) => s.type === 'reaction'), [segments])
  const [urlById, setUrlById] = useState<Map<number, string>>(() => new Map())
  const [catalogError, setCatalogError] = useState<string | null>(null)

  useEffect(() => {
    if (!needsCatalog) {
      return
    }
    let alive = true
    void (async () => {
      try {
        const cat = await loadReactionCatalog()
        if (!alive) return
        setUrlById(buildImageUrlMap(cat))
        setCatalogError(null)
      } catch (e) {
        if (!alive) return
        setCatalogError(e instanceof ApiError ? formatApiDetail(e.detail) : 'Реакции недоступны')
      }
    })()
    return () => {
      alive = false
    }
  }, [needsCatalog])

  if (segments.length === 0) {
    return null
  }

  return (
    <span className={className}>
      {catalogError != null ? (
        <span className="text-[11px] text-(--tgui--destructive_text_color)">{catalogError} · </span>
      ) : null}
      {segments.map((seg, i) => {
        if (seg.type === 'text') {
          return (
            <span key={`t-${i}`} className="whitespace-pre-wrap">
              {seg.value}
            </span>
          )
        }
        const src = urlById.get(seg.reactionTypeId)
        if (src == null) {
          return (
            <span key={`r-${i}`} className="inline-block align-[-0.15em] text-[13px] opacity-70" title="Реакция">
              ·
            </span>
          )
        }
        return (
          <img
            key={`r-${i}`}
            src={resolveApiMediaUrl(src)}
            alt=""
            className="mx-0.5 inline-block size-[1.4em] align-[-0.24em] object-contain"
            loading="lazy"
          />
        )
      })}
    </span>
  )
}
