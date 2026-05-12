/**
 * Maps a UTF-16 caret index in the raw draft string to pixel coordinates
 * inside a rich mirror (reaction images, mention chips) annotated with
 * `data-segment` + `data-char-start` / `data-char-end` (half-open range).
 */

function normalizeRangeRect(
  range: Range,
  fallbackLineHeightPx: number,
): { left: number; top: number; width: number; height: number } {
  let rect = range.getBoundingClientRect()
  if (rect.width === 0 && rect.height === 0) {
    const rects = range.getClientRects()
    if (rects.length > 0) {
      rect = rects[rects.length - 1]!
    }
  }
  const h = rect.height > 0 ? rect.height : fallbackLineHeightPx
  return { left: rect.left, top: rect.top, width: rect.width > 0 ? rect.width : 0, height: h }
}

function rectRelativeToPositionRoot(
  range: Range,
  positionRoot: HTMLElement,
  fallbackLineHeightPx: number,
): { left: number; top: number; height: number } {
  const rect = normalizeRangeRect(range, fallbackLineHeightPx)
  const rootRect = positionRoot.getBoundingClientRect()
  return {
    left: rect.left - rootRect.left,
    top: rect.top - rootRect.top,
    height: rect.height,
  }
}

function firstTextNode(el: HTMLElement): Text | null {
  const { firstChild } = el
  if (firstChild?.nodeType === Node.TEXT_NODE) {
    return firstChild as Text
  }
  return null
}

/**
 * @param mirrorRoot — scroll/transform container that holds annotated segments (query scope).
 * @param positionRoot — `position: relative` wrapper used for absolutely positioned fake caret.
 */
export function richMirrorCaretPositionInRoot(
  mirrorRoot: HTMLElement,
  positionRoot: HTMLElement,
  fullText: string,
  caret: number,
  fallbackLineHeightPx: number,
): { left: number; top: number; height: number } | null {
  const clamped = Math.max(0, Math.min(caret, fullText.length))
  const els = [...mirrorRoot.querySelectorAll('[data-segment][data-char-start][data-char-end]')] as HTMLElement[]
  if (els.length === 0) {
    return null
  }

  const range = document.createRange()

  if (clamped === fullText.length) {
    const last = els.at(-1)
    if (last == null) {
      return null
    }
    range.setStartAfter(last)
    range.collapse(true)
    return rectRelativeToPositionRoot(range, positionRoot, fallbackLineHeightPx)
  }

  for (const el of els) {
    const start = Number(el.dataset.charStart)
    const end = Number(el.dataset.charEnd)
    const seg = el.dataset.segment
    if (!Number.isFinite(start) || !Number.isFinite(end) || seg == null || seg === '') {
      continue
    }
    if (clamped < start) {
      break
    }
    if (clamped >= end) {
      continue
    }

    if (seg === 'text') {
      const tn = firstTextNode(el)
      if (tn != null) {
        const offset = clamped - start
        const o = Math.max(0, Math.min(offset, tn.length))
        range.setStart(tn, o)
        range.collapse(true)
        return rectRelativeToPositionRoot(range, positionRoot, fallbackLineHeightPx)
      }
      continue
    }

    if (seg === 'reaction' || seg === 'mention') {
      const mid = start + (end - start) / 2
      if (clamped < mid) {
        range.setStartBefore(el)
      } else {
        range.setStartAfter(el)
      }
      range.collapse(true)
      return rectRelativeToPositionRoot(range, positionRoot, fallbackLineHeightPx)
    }
  }

  return null
}
