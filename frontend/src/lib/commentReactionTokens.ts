/** Matches backend `services/cards/comment_reaction_tokens.COMMENT_TEXT_MAX_LEN`. */
export const COMMENT_BODY_MAX_LEN = 250

export function reactionTokenFromId(reactionTypeId: number): string {
  return `⟦r${reactionTypeId}⟧`
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

/** Canonical inline reaction marker (matches backend `REACTION_TOKEN_RE`). */
const UNICODE_TOKEN_RE = /⟦r(\d+)⟧/g
/** Legacy / mistyped ASCII bracket form sometimes stored or pasted as `[[r12]]`. */
const ASCII_TOKEN_RE = /\[\[r(\d+)\]\]/g
/** Feed @mention token `⟦@profile_slug⟧` (matches backend). */
const UNICODE_MENTION_RE = /⟦@([^⟧]+)⟧/g

type SegmentHit =
  | { index: number; len: number; kind: 'reaction'; reactionTypeId: number }
  | { index: number; len: number; kind: 'mention'; profileSlug: string }

/** Split stored comment (or watch note) text into plain text, reaction, and feed mention segments. */
export function splitCommentTextIntoSegments(text: string): CommentTextSegment[] {
  if (text === '') {
    return []
  }

  const hits: SegmentHit[] = []
  let m: RegExpExecArray | null

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

  hits.sort((a, b) => a.index - b.index)

  const segments: CommentTextSegment[] = []
  let lastIndex = 0
  for (const hit of hits) {
    if (hit.index < lastIndex) {
      continue
    }
    if (hit.index > lastIndex) {
      segments.push({ type: 'text', value: text.slice(lastIndex, hit.index) })
    }
    if (hit.kind === 'reaction') {
      segments.push({ type: 'reaction', reactionTypeId: hit.reactionTypeId })
    } else {
      segments.push({ type: 'mention', profileSlug: hit.profileSlug })
    }
    lastIndex = hit.index + hit.len
  }
  if (lastIndex < text.length) {
    segments.push({ type: 'text', value: text.slice(lastIndex) })
  }
  return segments
}

export function insertSnippetAtCaret(
  value: string,
  selectionStart: number | null,
  selectionEnd: number | null,
  snippet: string,
  maxLen: number,
): { nextValue: string; caret: number } | null {
  const start = selectionStart ?? value.length
  const end = selectionEnd ?? value.length
  const nextValue = `${value.slice(0, start)}${snippet}${value.slice(end)}`
  if (nextValue.length > maxLen) {
    return null
  }
  return { nextValue, caret: start + snippet.length }
}
