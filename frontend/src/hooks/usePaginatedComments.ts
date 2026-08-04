import { useCallback, useEffect, useMemo, useRef, useState, type Dispatch, type SetStateAction } from 'react'

import { ApiError, formatApiDetail } from '../api/client'
import type { CommentPage, ThreadComment } from '../lib/commentThreadTypes'

export type PaginatedCommentsMode = 'all' | 'page'

type UsePaginatedCommentsArgs<T extends ThreadComment> = {
  enabled: boolean
  mode: PaginatedCommentsMode
  fetchPage: (params: { cursor: string | null; limit: number }) => Promise<CommentPage<T>>
  fetchAll?: () => Promise<T[]>
  pageLimit?: number
  loadErrorMessage?: string
}

type UsePaginatedCommentsResult<T extends ThreadComment> = {
  comments: T[]
  setComments: Dispatch<SetStateAction<T[]>>
  commentsNextCursor: string | null
  setCommentsNextCursor: Dispatch<SetStateAction<string | null>>
  commentsById: Map<number, T>
  commentsLoading: boolean
  commentsError: string | null
  setCommentsError: Dispatch<SetStateAction<string | null>>
  loadComments: (append: boolean) => Promise<void>
  reloadComments: () => Promise<void>
}

export function usePaginatedComments<T extends ThreadComment>({
  enabled,
  mode,
  fetchPage,
  fetchAll,
  pageLimit = 20,
  loadErrorMessage = 'Не удалось загрузить комментарии',
}: UsePaginatedCommentsArgs<T>): UsePaginatedCommentsResult<T> {
  const [comments, setComments] = useState<T[]>([])
  const [commentsNextCursor, setCommentsNextCursor] = useState<string | null>(null)
  const [commentsLoading, setCommentsLoading] = useState(false)
  const [commentsError, setCommentsError] = useState<string | null>(null)
  const commentsNextCursorRef = useRef<string | null>(commentsNextCursor)

  useEffect(() => {
    commentsNextCursorRef.current = commentsNextCursor
  }, [commentsNextCursor])

  const commentsById = useMemo(() => {
    const map = new Map<number, T>()
    comments.forEach((comment) => {
      map.set(comment.id, comment)
    })
    return map
  }, [comments])

  const loadComments = useCallback(
    async (append: boolean) => {
      if (!enabled) return
      const cursor = append ? commentsNextCursorRef.current : null
      if (append && cursor == null) return

      setCommentsLoading(true)
      if (!append) {
        setCommentsError(null)
      }
      try {
        if (!append && mode === 'all') {
          if (fetchAll == null) {
            throw new Error('usePaginatedComments: fetchAll is required when mode is "all"')
          }
          const items = await fetchAll()
          setComments(items)
          setCommentsNextCursor(null)
          return
        }
        const page = await fetchPage({ cursor, limit: pageLimit })
        setComments((prev) => (append ? [...prev, ...page.items] : page.items))
        setCommentsNextCursor(page.next_cursor ?? null)
      } catch (e) {
        if (e instanceof ApiError) {
          setCommentsError(formatApiDetail(e.detail))
        } else {
          setCommentsError(loadErrorMessage)
        }
      } finally {
        setCommentsLoading(false)
      }
    },
    [enabled, fetchAll, fetchPage, loadErrorMessage, mode, pageLimit],
  )

  const reloadComments = useCallback(async () => {
    await loadComments(false)
  }, [loadComments])

  const loadCommentsRef = useRef(loadComments)

  useEffect(() => {
    loadCommentsRef.current = loadComments
  }, [loadComments])

  useEffect(() => {
    if (!enabled) return
    let alive = true
    void (async () => {
      if (!alive) return
      await loadCommentsRef.current(false)
    })()
    return () => {
      alive = false
    }
  }, [enabled, fetchPage, fetchAll, mode, pageLimit])

  return {
    comments,
    setComments,
    commentsNextCursor,
    setCommentsNextCursor,
    commentsById,
    commentsLoading,
    commentsError,
    setCommentsError,
    loadComments,
    reloadComments,
  }
}
