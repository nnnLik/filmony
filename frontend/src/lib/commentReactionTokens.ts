/** Matches backend `services/cards/comment_reaction_tokens.COMMENT_TEXT_MAX_LEN`. */
export const COMMENT_BODY_MAX_LEN = 250

export function reactionTokenFromId(reactionTypeId: number): string {
  return `⟦r${reactionTypeId}⟧`
}

export type CommentTextSegment =
  | { type: 'text'; value: string }
  | { type: 'reaction'; reactionTypeId: number }

/** Split stored comment text into plain text and reaction token segments. */
export function splitCommentTextIntoSegments(text: string): CommentTextSegment[] {
  if (text === '') {
    return []
  }
  const segments: CommentTextSegment[] = []
  const re = /⟦r(\d+)⟧/g
  let lastIndex = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(text)) != null) {
    if (m.index > lastIndex) {
      segments.push({ type: 'text', value: text.slice(lastIndex, m.index) })
    }
    const id = Number(m[1])
    if (Number.isInteger(id) && id > 0) {
      segments.push({ type: 'reaction', reactionTypeId: id })
    } else {
      segments.push({ type: 'text', value: m[0] })
    }
    lastIndex = m.index + m[0].length
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
