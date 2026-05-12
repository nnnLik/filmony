import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import type { ReactionGroupedCatalog } from '../../api/profileTypes'
import { ApiError, formatApiDetail } from '../../api/client'
import { useMentionProfileLookup } from '../../hooks/useMentionProfileLookup'
import {
  splitCommentTextIntoSegmentsWithRanges,
  type CommentTextSegmentWithRange,
} from '../../lib/commentReactionTokens'
import type { InlineMovieCardRefMeta } from '../../lib/inlineMovieCardRefMap'
import { mentionHandleForDisplay } from '../../lib/mentionProfileLookupUtils'
import { loadReactionCatalog } from '../../lib/reactionCatalogCache'
import { resolveApiMediaUrl } from '../../lib/resolveApiMediaUrl'

const MENTION_CHIP_CLASS =
  'mx-0.5 inline-block rounded-md border border-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_50%,transparent)] bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_14%,transparent)] px-1 py-0.5 align-[-0.12em] text-[0.92em] font-semibold tabular-nums text-(--tgui--text_color) no-underline transition-opacity hover:opacity-95 active:opacity-90'

const CARD_CHIP_CLASS =
  'mx-0.5 inline-block max-w-[min(92vw,18rem)] truncate rounded-md border border-[color-mix(in_srgb,#f87171_52%,transparent)] bg-[color-mix(in_srgb,#f87171_14%,transparent)] px-1 py-0.5 align-[-0.12em] text-[0.92em] font-semibold tabular-nums text-(--tgui--text_color) no-underline transition-opacity hover:opacity-95 active:opacity-90'

const INLINE_CARD_UNAVAILABLE = 'Карточка недоступна'

type CommentBodyWithReactionTokensProps = {
  text: string
  className?: string
  /**
   * Adds `data-segment` + `data-char-start` / `data-char-end` (UTF-16 half-open) on each segment
   * so draft overlays can position a fake caret over rich markup.
   */
  annotateCharRanges?: boolean
  /** Разрешённые подписи для токенов ⟦c{id}⟧ (из API или локально при наборе). */
  inlineMovieCardRefs?: ReadonlyMap<number, InlineMovieCardRefMeta>
}

function buildImageUrlMap(catalog: ReactionGroupedCatalog): Map<number, string> {
  const m = new Map<number, string>()
  for (const tab of catalog.tabs) {
    for (const it of tab.items) {
      m.set(it.id, it.image_url)
    }
  }
  return m
}

function segmentDomAttrs(
  seg: CommentTextSegmentWithRange,
  kind: 'text' | 'reaction' | 'mention' | 'card_ref',
  on: boolean,
): Record<string, string> {
  if (!on) {
    return {}
  }
  return {
    'data-segment': kind,
    'data-char-start': String(seg.rangeStart),
    'data-char-end': String(seg.rangeEnd),
  }
}

export function CommentBodyWithReactionTokens({
  text,
  className,
  annotateCharRanges = false,
  inlineMovieCardRefs,
}: CommentBodyWithReactionTokensProps) {
  const mentionProfiles = useMentionProfileLookup()
  const segments = useMemo(() => splitCommentTextIntoSegmentsWithRanges(text), [text])
  const needsCatalog = useMemo(
    () => segments.some((s) => s.type === 'reaction'),
    [segments],
  )
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
      {catalogError != null && !annotateCharRanges ? (
        <span className="text-[11px] text-(--tgui--destructive_text_color)">{catalogError} · </span>
      ) : null}
      {segments.map((seg, i) => {
        if (seg.type === 'text') {
          return (
            <span key={`t-${i}`} className="whitespace-pre-wrap" {...segmentDomAttrs(seg, 'text', annotateCharRanges)}>
              {seg.value}
            </span>
          )
        }
        if (seg.type === 'mention') {
          const row = mentionProfiles.get(seg.profileSlug)
          const handle = mentionHandleForDisplay(row?.username, seg.profileSlug)
          const label = `@${handle}`
          const slugTitle = `@${seg.profileSlug}`
          if (!annotateCharRanges) {
            if (row != null) {
              return (
                <Link
                  key={`m-${i}`}
                  to={`/u/${encodeURIComponent(row.userId)}`}
                  className={MENTION_CHIP_CLASS}
                  title={row.username?.trim() ? `${label} (${slugTitle})` : slugTitle}
                  aria-label={`Профиль ${label}`}
                  onClick={(e) => e.stopPropagation()}
                >
                  {label}
                </Link>
              )
            }
            return (
              <span key={`m-${i}`} className={MENTION_CHIP_CLASS} title={slugTitle}>
                {label}
              </span>
            )
          }
          const mentionInner =
            row != null ? (
              <Link
                to={`/u/${encodeURIComponent(row.userId)}`}
                className={MENTION_CHIP_CLASS}
                title={row.username?.trim() ? `${label} (${slugTitle})` : slugTitle}
                aria-label={`Профиль ${label}`}
                onClick={(e) => e.stopPropagation()}
              >
                {label}
              </Link>
            ) : (
              <span className={MENTION_CHIP_CLASS} title={slugTitle}>
                {label}
              </span>
            )
          return (
            <span key={`m-${i}`} className="inline" {...segmentDomAttrs(seg, 'mention', true)}>
              {mentionInner}
            </span>
          )
        }
        if (seg.type === 'card_ref') {
          const meta = inlineMovieCardRefs?.get(seg.movieCardId)
          const title = meta?.film_title ?? INLINE_CARD_UNAVAILABLE
          const yearSuffix = meta?.film_year != null ? ` (${meta.film_year})` : ''
          const display = `${title}${yearSuffix}`
          const chip = (
            <Link
              to={`/cards/${seg.movieCardId}`}
              className={CARD_CHIP_CLASS}
              title={display}
              aria-label={`Карточка: ${display}`}
              onClick={(e) => e.stopPropagation()}
            >
              {title}
              {meta?.film_year != null ? <span className="font-normal opacity-90"> · {meta.film_year}</span> : null}
            </Link>
          )
          if (!annotateCharRanges) {
            return (
              <span key={`c-${i}`} className="inline">
                {chip}
              </span>
            )
          }
          return (
            <span key={`c-${i}`} className="inline" {...segmentDomAttrs(seg, 'card_ref', true)}>
              {chip}
            </span>
          )
        }
        const src = urlById.get(seg.reactionTypeId)
        if (src == null) {
          return (
            <span
              key={`r-${i}`}
              className="inline-block align-[-0.15em] text-[13px] opacity-70"
              title="Реакция"
              {...segmentDomAttrs(seg, 'reaction', annotateCharRanges)}
            >
              ·
            </span>
          )
        }
        return (
          <span
            key={`r-${i}`}
            className="inline-block align-[-0.24em]"
            {...segmentDomAttrs(seg, 'reaction', annotateCharRanges)}
          >
            <img
              src={resolveApiMediaUrl(src)}
              alt=""
              className="mx-0.5 inline-block size-[1.4em] align-[-0.24em] object-contain"
              loading="lazy"
            />
          </span>
        )
      })}
    </span>
  )
}
