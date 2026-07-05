/** Matches backend `services/text/spoiler_tokens`. */
export const SPOILER_OPEN = '⟦S⟧'
export const SPOILER_CLOSE = '⟦/S⟧'

export type SpoilerTextPart =
  | { type: 'plain'; value: string; rangeStart: number; rangeEnd: number }
  | { type: 'spoiler'; value: string; rangeStart: number; rangeEnd: number }

const SPOILER_PLACEHOLDER = 'спойлер'

export function splitTextWithSpoilers(text: string): SpoilerTextPart[] {
  if (text === '') {
    return []
  }

  const parts: SpoilerTextPart[] = []
  let cursor = 0

  while (cursor < text.length) {
    const openIdx = text.indexOf(SPOILER_OPEN, cursor)
    if (openIdx === -1) {
      parts.push({
        type: 'plain',
        value: text.slice(cursor),
        rangeStart: cursor,
        rangeEnd: text.length,
      })
      break
    }

    if (openIdx > cursor) {
      parts.push({
        type: 'plain',
        value: text.slice(cursor, openIdx),
        rangeStart: cursor,
        rangeEnd: openIdx,
      })
    }

    const innerStart = openIdx + SPOILER_OPEN.length
    const closeIdx = text.indexOf(SPOILER_CLOSE, innerStart)
    if (closeIdx === -1) {
      parts.push({
        type: 'plain',
        value: text.slice(openIdx),
        rangeStart: openIdx,
        rangeEnd: text.length,
      })
      break
    }

    parts.push({
      type: 'spoiler',
      value: text.slice(innerStart, closeIdx),
      rangeStart: openIdx,
      rangeEnd: closeIdx + SPOILER_CLOSE.length,
    })
    cursor = closeIdx + SPOILER_CLOSE.length
  }

  return parts
}

function isSelectionWrappedBySpoiler(value: string, start: number, end: number, selected: string): boolean {
  if (selected.startsWith(SPOILER_OPEN) && selected.endsWith(SPOILER_CLOSE)) {
    return true
  }
  const before = value.slice(0, start)
  const after = value.slice(end)
  return before.endsWith(SPOILER_OPEN) && after.startsWith(SPOILER_CLOSE)
}

function unwrapSpoilerSelection(value: string, start: number, end: number, selected: string): { nextValue: string; caret: number } {
  if (selected.startsWith(SPOILER_OPEN) && selected.endsWith(SPOILER_CLOSE)) {
    const inner = selected.slice(SPOILER_OPEN.length, selected.length - SPOILER_CLOSE.length)
    const nextValue = `${value.slice(0, start)}${inner}${value.slice(end)}`
    return { nextValue, caret: start + inner.length }
  }

  const before = value.slice(0, start)
  const after = value.slice(end)
  const nextValue = `${before.slice(0, before.length - SPOILER_OPEN.length)}${selected}${after.slice(SPOILER_CLOSE.length)}`
  return { nextValue, caret: start - SPOILER_OPEN.length + selected.length }
}

/** Wrap selected text as spoiler, unwrap if already wrapped, or insert empty spoiler template. */
export function toggleSpoilerAtSelection(
  value: string,
  selectionStart: number | null,
  selectionEnd: number | null,
  maxLen: number,
): { nextValue: string; caret: number } | null {
  const start = selectionStart ?? value.length
  const end = selectionEnd ?? value.length
  const selected = value.slice(start, end)

  if (start === end) {
    const snippet = `${SPOILER_OPEN}${SPOILER_PLACEHOLDER}${SPOILER_CLOSE}`
    const nextValue = `${value.slice(0, start)}${snippet}${value.slice(end)}`
    if (nextValue.length > maxLen) {
      return null
    }
    return {
      nextValue,
      caret: start + SPOILER_OPEN.length + SPOILER_PLACEHOLDER.length,
    }
  }

  if (isSelectionWrappedBySpoiler(value, start, end, selected)) {
    const unwrapped = unwrapSpoilerSelection(value, start, end, selected)
    if (unwrapped.nextValue.length > maxLen) {
      return null
    }
    return unwrapped
  }

  const wrapped = `${SPOILER_OPEN}${selected}${SPOILER_CLOSE}`
  const nextValue = `${value.slice(0, start)}${wrapped}${value.slice(end)}`
  if (nextValue.length > maxLen) {
    return null
  }
  return { nextValue, caret: start + wrapped.length }
}
