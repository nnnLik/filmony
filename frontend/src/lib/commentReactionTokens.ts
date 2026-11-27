/** Matches backend `services/cards/comment_reaction_tokens.COMMENT_TEXT_MAX_LEN`. */
export const COMMENT_BODY_MAX_LEN = 250

export function reactionTokenFromId(reactionTypeId: number): string {
  return `⟦r${reactionTypeId}⟧`
}

export function reactionTokenFromShortcode(shortcode: string): string {
  return `:${shortcode}:`
}

/** Prefer `:shortcode:` when the catalog name is known; otherwise legacy `⟦r{id}⟧`. */
export function reactionTokenForInsert(id: number, shortcode: string | undefined): string {
  if (shortcode != null && shortcode !== '') {
    return reactionTokenFromShortcode(shortcode)
  }
  return reactionTokenFromId(id)
}

/** Inline reference to viewer's card (matches backend `inline_movie_card_ref_tokens`). */
export function movieCardRefTokenFromId(movieCardId: number): string {
  const id = Math.floor(movieCardId)
  if (!Number.isFinite(id) || id < 1) {
    throw new RangeError('invalid card id')
  }
  return `⟦c${id}⟧`
}

/** Canonical feed mention (matches backend `validate_feed_post_body`). */
export function mentionTokenFromProfileSlug(slug: string): string {
  const s = slug.trim().toLowerCase()
  return `⟦@${s}⟧`
}

export type CommentTextSegment =
  | { type: 'text'; value: string }
  | { type: 'reaction'; reactionTypeId: number }
  | { type: 'mention'; profileSlug: string }
  | { type: 'card_ref'; movieCardId: number }

export type CommentTextSegmentWithRange =
  | { type: 'text'; value: string; rangeStart: number; rangeEnd: number }
  | { type: 'reaction'; reactionTypeId: number; rangeStart: number; rangeEnd: number }
  | { type: 'mention'; profileSlug: string; rangeStart: number; rangeEnd: number }
  | { type: 'card_ref'; movieCardId: number; rangeStart: number; rangeEnd: number }

/** Canonical inline reaction marker (matches backend `REACTION_TOKEN_RE`). */
const UNICODE_TOKEN_RE = /⟦r(\d+)⟧/g
/** Legacy / mistyped ASCII bracket form sometimes stored or pasted as `[[r12]]`. */
const ASCII_TOKEN_RE = /\[\[r(\d+)\]\]/g
/** Readable `:shortcode:` (matches backend `SHORTCODE_TOKEN_RE`); reaction only if in catalog map. */
const SHORTCODE_TOKEN_RE = /:([a-z][a-z0-9_+-]{0,31}):/g
/** Feed @mention token `⟦@profile_slug⟧` (matches backend). */
const UNICODE_MENTION_RE = /⟦@([^⟧]+)⟧/g
/** Own card ref `⟦c{id}⟧` (matches backend). */
const UNICODE_CARD_REF_RE = /⟦c(\d+)⟧/g

type SegmentHit =
  | { index: number; len: number; kind: 'reaction'; reactionTypeId: number }
  | { index: number; len: number; kind: 'mention'; profileSlug: string }
  | { index: number; len: number; kind: 'card_ref'; movieCardId: number }

function collectSegmentHits(
  text: string,
  shortcodeToId?: ReadonlyMap<string, number>,
): SegmentHit[] {
  const hits: SegmentHit[] = []
  let m: RegExpExecArray | null

  if (shortcodeToId != null) {
    SHORTCODE_TOKEN_RE.lastIndex = 0
    while ((m = SHORTCODE_TOKEN_RE.exec(text)) != null) {
      const name = m[1]
      if (name == null) {
        continue
      }
      const id = shortcodeToId.get(name)
      if (id != null && Number.isInteger(id) && id > 0) {
        hits.push({
          index: m.index,
          len: m[0].length,
          kind: 'reaction',
          reactionTypeId: id,
        })
      }
    }
  }

  UNICODE_TOKEN_RE.lastIndex = 0
  while ((m = UNICODE_TOKEN_RE.exec(text)) != null) {
    const id = Number(m[1])
    if (Number.isInteger(id) && id > 0) {
      hits.push({
        index: m.index,
        len: m[0].length,
        kind: 'reaction',
        reactionTypeId: id,
      })
    }
  }

  ASCII_TOKEN_RE.lastIndex = 0
  while ((m = ASCII_TOKEN_RE.exec(text)) != null) {
    const id = Number(m[1])
    if (Number.isInteger(id) && id > 0) {
      hits.push({
        index: m.index,
        len: m[0].length,
        kind: 'reaction',
        reactionTypeId: id,
      })
    }
  }

  UNICODE_MENTION_RE.lastIndex = 0
  while ((m = UNICODE_MENTION_RE.exec(text)) != null) {
    const slug = m[1].trim().toLowerCase()
    if (slug.length > 0) {
      hits.push({
        index: m.index,
        len: m[0].length,
        kind: 'mention',
        profileSlug: slug,
      })
    }
  }

  UNICODE_CARD_REF_RE.lastIndex = 0
  while ((m = UNICODE_CARD_REF_RE.exec(text)) != null) {
    const id = Number(m[1])
    if (Number.isInteger(id) && id > 0) {
      hits.push({
        index: m.index,
        len: m[0].length,
        kind: 'card_ref',
        movieCardId: id,
      })
    }
  }

  hits.sort((a, b) => a.index - b.index)
  return hits
}

function splitCommentTextIntoSegmentsWithRangesImpl(
  text: string,
  shortcodeToId?: ReadonlyMap<string, number>,
): CommentTextSegmentWithRange[] {
  if (text === '') {
    return []
  }

  const hits = collectSegmentHits(text, shortcodeToId)
  const segments: CommentTextSegmentWithRange[] = []
  let lastIndex = 0
  for (const hit of hits) {
    if (hit.index < lastIndex) {
      continue
    }
    if (hit.index > lastIndex) {
      segments.push({
        type: 'text',
        value: text.slice(lastIndex, hit.index),
        rangeStart: lastIndex,
        rangeEnd: hit.index,
      })
    }
    const tokEnd = hit.index + hit.len
    if (hit.kind === 'reaction') {
      segments.push({
        type: 'reaction',
        reactionTypeId: hit.reactionTypeId,
        rangeStart: hit.index,
        rangeEnd: tokEnd,
      })
    } else if (hit.kind === 'mention') {
      segments.push({
        type: 'mention',
        profileSlug: hit.profileSlug,
        rangeStart: hit.index,
        rangeEnd: tokEnd,
      })
    } else {
      segments.push({
        type: 'card_ref',
        movieCardId: hit.movieCardId,
        rangeStart: hit.index,
        rangeEnd: tokEnd,
      })
    }
    lastIndex = tokEnd
  }
  if (lastIndex < text.length) {
    segments.push({
      type: 'text',
      value: text.slice(lastIndex),
      rangeStart: lastIndex,
      rangeEnd: text.length,
    })
  }
  return segments
}

function segmentToPlain(s: CommentTextSegmentWithRange): CommentTextSegment {
  if (s.type === 'text') {
    return { type: 'text', value: s.value }
  }
  if (s.type === 'reaction') {
    return { type: 'reaction', reactionTypeId: s.reactionTypeId }
  }
  if (s.type === 'mention') {
    return { type: 'mention', profileSlug: s.profileSlug }
  }
  return { type: 'card_ref', movieCardId: s.movieCardId }
}

/** Split stored comment (or watch note) text into plain text, reaction, and feed mention segments. */
export function splitCommentTextIntoSegments(
  text: string,
  shortcodeToId?: ReadonlyMap<string, number>,
): CommentTextSegment[] {
  return splitCommentTextIntoSegmentsWithRangesImpl(text, shortcodeToId).map(segmentToPlain)
}

/** Same as {@link splitCommentTextIntoSegments} plus UTF-16 half-open `[rangeStart, rangeEnd)` spans in the source string. */
export function splitCommentTextIntoSegmentsWithRanges(
  text: string,
  shortcodeToId?: ReadonlyMap<string, number>,
): CommentTextSegmentWithRange[] {
  return splitCommentTextIntoSegmentsWithRangesImpl(text, shortcodeToId)
}

const UNICODE_EXPAND_RE = /⟦r(\d+)⟧/g
const ASCII_EXPAND_RE = /\[\[r(\d+)\]\]/g

/** Replace legacy `⟦r{id}⟧` / `[[r{id}]]` with `:shortcode:` when the id is in the map. */
export function expandLegacyReactionTokens(
  text: string,
  idToShortcode: ReadonlyMap<number, string>,
): string {
  const replaceKnown = (full: string, idRaw: string): string => {
    const id = Number(idRaw)
    const shortcode = idToShortcode.get(id)
    if (shortcode == null || shortcode === '') {
      return full
    }
    return `:${shortcode}:`
  }
  UNICODE_EXPAND_RE.lastIndex = 0
  ASCII_EXPAND_RE.lastIndex = 0
  return text.replace(UNICODE_EXPAND_RE, replaceKnown).replace(ASCII_EXPAND_RE, replaceKnown)
}

export function insertSnippetAtCaret(
  value: string,
  selectionStart: number | null,
  selectionEnd: number | null,
  snippet: string,
  maxLen?: number,
): { nextValue: string; caret: number } | null {
  const start = selectionStart ?? value.length
  const end = selectionEnd ?? value.length
  const nextValue = `${value.slice(0, start)}${snippet}${value.slice(end)}`
  if (maxLen != null && nextValue.length > maxLen) {
    return null
  }
  return { nextValue, caret: start + snippet.length }
}
