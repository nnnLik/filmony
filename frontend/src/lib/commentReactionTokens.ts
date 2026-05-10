/** Matches backend `services/cards/comment_reaction_tokens.COMMENT_TEXT_MAX_LEN`. */
export const COMMENT_BODY_MAX_LEN = 250

export function reactionTokenFromId(reactionTypeId: number): string {
  return `⟦r${reactionTypeId}⟧`
}

export type CommentTextSegment =
  | { type: 'text'; value: string }
  | { type: 'reaction'; reactionTypeId: number }

/** Canonical inline reaction marker (matches backend `REACTION_TOKEN_RE`). */
const UNICODE_TOKEN_RE = /⟦r(\d+)⟧/g
/** Legacy / mistyped ASCII bracket form sometimes stored or pasted as `[[r12]]`. */
const ASCII_TOKEN_RE = /\[\[r(\d+)\]\]/g

/** Split stored comment (or watch note) text into plain text and reaction token segments. */
export function splitCommentTextIntoSegments(text: string): CommentTextSegment[] {
  if (text === '') {
    return []
  }

  const hits: Array<{ index: number; len: number; id: number }> = []
  let m: RegExpExecArray | null

  UNICODE_TOKEN_RE.lastIndex = 0
  while ((m = UNICODE_TOKEN_RE.exec(text)) != null) {
    const id = Number(m[1])
    if (Number.isInteger(id) && id > 0) {
      hits.push({ index: m.index, len: m[0].length, id })
    }
  }

  ASCII_TOKEN_RE.lastIndex = 0
  while ((m = ASCII_TOKEN_RE.exec(text)) != null) {
    const id = Number(m[1])
    if (Number.isInteger(id) && id > 0) {
      hits.push({ index: m.index, len: m[0].length, id })
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
    segments.push({ type: 'reaction', reactionTypeId: hit.id })
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
