import { useCallback, useRef, useState } from 'react'

const HIGHLIGHT_MS = 1700

export function useCommentScrollHighlight() {
  const commentRefs = useRef<Record<number, HTMLDivElement | null>>({})
  const [highlightCommentId, setHighlightCommentId] = useState<number | null>(null)

  const setCommentRef = useCallback((commentId: number, element: HTMLDivElement | null) => {
    commentRefs.current[commentId] = element
  }, [])

  const scrollToComment = useCallback((commentId: number): boolean => {
    const target = commentRefs.current[commentId]
    if (target == null) return false
    target.scrollIntoView({ behavior: 'smooth', block: 'center' })
    setHighlightCommentId(commentId)
    window.setTimeout(() => {
      setHighlightCommentId((prev) => (prev === commentId ? null : prev))
    }, HIGHLIGHT_MS)
    return true
  }, [])

  return {
    commentRefs,
    highlightCommentId,
    setCommentRef,
    scrollToComment,
  }
}
