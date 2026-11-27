/** Matches backend `services/text/spoiler_tokens`. */
export const SPOILER_OPEN = '⟦S⟧'
export const SPOILER_CLOSE = '⟦/S⟧'
export const PIPE_SPOILER_MARK = '||'

export type SpoilerTextPart =
  | { type: 'plain'; value: string; rangeStart: number; rangeEnd: number }
  | {
      type: 'spoiler'
      value: string
      rangeStart: number
      rangeEnd: number
      openMarker: string
      closeMarker: string
    }

const SPOILER_PLACEHOLDER = 'спойлер'

type SpoilerMarkerKind = 'pipe' | 'legacy'

function nextSpoilerOpen(
  text: string,
  from: number,
): { index: number; kind: SpoilerMarkerKind } | null {
  const pipeIdx = text.indexOf(PIPE_SPOILER_MARK, from)
  const legacyIdx = text.indexOf(SPOILER_OPEN, from)
  if (pipeIdx === -1 && legacyIdx === -1) {
    return null
  }
  if (legacyIdx === -1 || (pipeIdx !== -1 && pipeIdx < legacyIdx)) {
    return { index: pipeIdx, kind: 'pipe' }
  }
  return { index: legacyIdx, kind: 'legacy' }
}

export function splitTextWithSpoilers(text: string): SpoilerTextPart[] {
  if (text === '') {
    return []
  }

  const parts: SpoilerTextPart[] = []
  let cursor = 0

  while (cursor < text.length) {
    const open = nextSpoilerOpen(text, cursor)
    if (open == null) {
      parts.push({
        type: 'plain',
        value: text.slice(cursor),
        rangeStart: cursor,
        rangeEnd: text.length,
      })
      break
    }

    if (open.index > cursor) {
      parts.push({
        type: 'plain',
        value: text.slice(cursor, open.index),
        rangeStart: cursor,
        rangeEnd: open.index,
      })
    }

    if (open.kind === 'pipe') {
      const innerStart = open.index + PIPE_SPOILER_MARK.length
      const closeIdx = text.indexOf(PIPE_SPOILER_MARK, innerStart)
      if (closeIdx === -1) {
        parts.push({
          type: 'plain',
          value: text.slice(open.index),
          rangeStart: open.index,
          rangeEnd: text.length,
        })
        break
      }
      parts.push({
        type: 'spoiler',
        value: text.slice(innerStart, closeIdx),
        rangeStart: open.index,
        rangeEnd: closeIdx + PIPE_SPOILER_MARK.length,
        openMarker: PIPE_SPOILER_MARK,
        closeMarker: PIPE_SPOILER_MARK,
      })
      cursor = closeIdx + PIPE_SPOILER_MARK.length
      continue
    }

    const innerStart = open.index + SPOILER_OPEN.length
    const closeIdx = text.indexOf(SPOILER_CLOSE, innerStart)
    if (closeIdx === -1) {
      parts.push({
        type: 'plain',
        value: text.slice(open.index),
        rangeStart: open.index,
        rangeEnd: text.length,
      })
      break
    }
    parts.push({
      type: 'spoiler',
      value: text.slice(innerStart, closeIdx),
      rangeStart: open.index,
      rangeEnd: closeIdx + SPOILER_CLOSE.length,
      openMarker: SPOILER_OPEN,
      closeMarker: SPOILER_CLOSE,
    })
    cursor = closeIdx + SPOILER_CLOSE.length
  }

  return parts
}

type MarkerPair = { open: string; close: string }

const PIPE_PAIR: MarkerPair = { open: PIPE_SPOILER_MARK, close: PIPE_SPOILER_MARK }
const LEGACY_PAIR: MarkerPair = { open: SPOILER_OPEN, close: SPOILER_CLOSE }

function isSelectionWrappedByPair(
  value: string,
  start: number,
  end: number,
  selected: string,
  pair: MarkerPair,
): boolean {
  if (
    selected.length >= pair.open.length + pair.close.length &&
    selected.startsWith(pair.open) &&
    selected.endsWith(pair.close)
  ) {
    return true
  }
  const before = value.slice(0, start)
  const after = value.slice(end)
  return before.endsWith(pair.open) && after.startsWith(pair.close)
}

function isSelectionWrappedBySpoiler(value: string, start: number, end: number, selected: string): boolean {
  return (
    isSelectionWrappedByPair(value, start, end, selected, PIPE_PAIR) ||
    isSelectionWrappedByPair(value, start, end, selected, LEGACY_PAIR)
  )
}

function unwrapSpoilerSelectionWithPair(
  value: string,
  start: number,
  end: number,
  selected: string,
  pair: MarkerPair,
): { nextValue: string; caret: number } {
  if (
    selected.length >= pair.open.length + pair.close.length &&
    selected.startsWith(pair.open) &&
    selected.endsWith(pair.close)
  ) {
    const inner = selected.slice(pair.open.length, selected.length - pair.close.length)
    const nextValue = `${value.slice(0, start)}${inner}${value.slice(end)}`
    return { nextValue, caret: start + inner.length }
  }

  const before = value.slice(0, start)
  const after = value.slice(end)
  const nextValue = `${before.slice(0, before.length - pair.open.length)}${selected}${after.slice(pair.close.length)}`
  return { nextValue, caret: start - pair.open.length + selected.length }
}

function unwrapSpoilerSelection(
  value: string,
  start: number,
  end: number,
  selected: string,
): { nextValue: string; caret: number } {
  if (isSelectionWrappedByPair(value, start, end, selected, PIPE_PAIR)) {
    return unwrapSpoilerSelectionWithPair(value, start, end, selected, PIPE_PAIR)
  }
  return unwrapSpoilerSelectionWithPair(value, start, end, selected, LEGACY_PAIR)
}

/** Wrap selected text as spoiler, unwrap if already wrapped, or insert empty spoiler template. */
export function toggleSpoilerAtSelection(
  value: string,
  selectionStart: number | null,
  selectionEnd: number | null,
  maxLen?: number,
): { nextValue: string; caret: number } | null {
  const start = selectionStart ?? value.length
  const end = selectionEnd ?? value.length
  const selected = value.slice(start, end)

  if (start === end) {
    const snippet = `${PIPE_SPOILER_MARK}${SPOILER_PLACEHOLDER}${PIPE_SPOILER_MARK}`
    const nextValue = `${value.slice(0, start)}${snippet}${value.slice(end)}`
    if (maxLen != null && nextValue.length > maxLen) {
      return null
    }
    return {
      nextValue,
      caret: start + PIPE_SPOILER_MARK.length + SPOILER_PLACEHOLDER.length,
    }
  }

  if (isSelectionWrappedBySpoiler(value, start, end, selected)) {
    const unwrapped = unwrapSpoilerSelection(value, start, end, selected)
    if (maxLen != null && unwrapped.nextValue.length > maxLen) {
      return null
    }
    return unwrapped
  }

  const wrapped = `${PIPE_SPOILER_MARK}${selected}${PIPE_SPOILER_MARK}`
  const nextValue = `${value.slice(0, start)}${wrapped}${value.slice(end)}`
  if (maxLen != null && nextValue.length > maxLen) {
    return null
  }
  return { nextValue, caret: start + wrapped.length }
}
