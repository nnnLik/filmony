import { useCallback, useEffect, useMemo, useState, type Dispatch, type SetStateAction } from 'react'

import { ApiError, formatApiDetail } from '../api/client'
import type { ThreadComment } from '../lib/commentThreadTypes'

type UseFeedInlineCommentsPanelArgs<T extends ThreadComment> = {
  postId: number
  commentsCount: number
  open: boolean
  enabled?: boolean
  listAllComments: (postId: number) => Promise<T[]>
}

type UseFeedInlineCommentsPanelResult<T extends ThreadComment> = {
  panelComments: T[]
  setPanelComments: Dispatch<SetStateAction<T[]>>
  panelLoading: boolean
  panelError: string | null
  previewCommentsById: Map<number, T>
  resetPanel: () => void
}

export function useFeedInlineCommentsPanel<T extends ThreadComment>({
  postId,
  commentsCount,
  open,
  enabled = true,
  listAllComments,
}: UseFeedInlineCommentsPanelArgs<T>): UseFeedInlineCommentsPanelResult<T> {
  const [panelComments, setPanelComments] = useState<T[]>([])
  const [panelLoading, setPanelLoading] = useState(false)
  const [panelError, setPanelError] = useState<string | null>(null)

  const previewCommentsById = useMemo(() => {
    const map = new Map<number, T>()
    panelComments.forEach((comment) => {
      map.set(comment.id, comment)
    })
    return map
  }, [panelComments])

  const resetPanel = useCallback(() => {
    setPanelComments([])
    setPanelLoading(false)
    setPanelError(null)
  }, [])

  useEffect(() => {
    let cancelled = false
    if (!enabled || !open || commentsCount === 0) {
      void Promise.resolve().then(() => {
        if (cancelled) return
        resetPanel()
      })
      return () => {
        cancelled = true
      }
    }

    void Promise.resolve().then(() => {
      if (!cancelled) {
        setPanelLoading(true)
        setPanelError(null)
      }
    })

    void listAllComments(postId).then(
      (items) => {
        if (!cancelled) {
          setPanelComments(items)
          setPanelLoading(false)
        }
      },
      (error) => {
        if (!cancelled) {
          setPanelComments([])
          setPanelError(
            error instanceof ApiError ? formatApiDetail(error.detail) : 'Не удалось загрузить комментарии',
          )
          setPanelLoading(false)
        }
      },
    )

    return () => {
      cancelled = true
    }
  }, [commentsCount, enabled, listAllComments, open, postId, resetPanel])

  return {
    panelComments,
    setPanelComments,
    panelLoading,
    panelError,
    previewCommentsById,
    resetPanel,
  }
}
