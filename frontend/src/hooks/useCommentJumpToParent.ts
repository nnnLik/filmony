import { useCallback, useState, type Dispatch, type SetStateAction } from 'react'

import { ApiError, formatApiDetail } from '../api/client'
import type { CommentPage, ThreadComment } from '../lib/commentThreadTypes'

type UseCommentJumpToParentArgs<T extends ThreadComment> = {
  comments: T[]
  commentsById: Map<number, T>
  commentsNextCursor: string | null
  setComments: Dispatch<SetStateAction<T[]>>
  setCommentsNextCursor: Dispatch<SetStateAction<string | null>>
  setCommentsError: Dispatch<SetStateAction<string | null>>
  fetchPage: (params: { cursor: string; limit: number }) => Promise<CommentPage<T>>
  scrollToComment: (commentId: number) => boolean
  pageLimit?: number
  notFoundMessage?: string
  loadErrorMessage?: string
}

type UseCommentJumpToParentResult = {
  jumpBusy: boolean
  handleJumpToParent: (parentCommentId: number) => Promise<void>
}

export function useCommentJumpToParent<T extends ThreadComment>({
  comments,
  commentsById,
  commentsNextCursor,
  setComments,
  setCommentsNextCursor,
  setCommentsError,
  fetchPage,
  scrollToComment,
  pageLimit = 20,
  notFoundMessage = 'Родительский комментарий не найден',
  loadErrorMessage = 'Не удалось загрузить родительский комментарий',
}: UseCommentJumpToParentArgs<T>): UseCommentJumpToParentResult {
  const [jumpBusy, setJumpBusy] = useState(false)

  const handleJumpToParent = useCallback(
    async (parentCommentId: number) => {
      if (jumpBusy) return
      setCommentsError(null)

      if (commentsById.has(parentCommentId)) {
        scrollToComment(parentCommentId)
        return
      }

      setJumpBusy(true)
      try {
        let cursor = commentsNextCursor
        let accumulated = comments
        while (cursor != null && !accumulated.some((item) => item.id === parentCommentId)) {
          const page = await fetchPage({ cursor, limit: pageLimit })
          accumulated = [...accumulated, ...page.items]
          cursor = page.next_cursor ?? null
        }
        setComments(accumulated)
        setCommentsNextCursor(cursor)

        if (!accumulated.some((item) => item.id === parentCommentId)) {
          setCommentsError(notFoundMessage)
          return
        }
        window.requestAnimationFrame(() => {
          scrollToComment(parentCommentId)
        })
      } catch (e) {
        if (e instanceof ApiError) {
          setCommentsError(formatApiDetail(e.detail))
        } else {
          setCommentsError(loadErrorMessage)
        }
      } finally {
        setJumpBusy(false)
      }
    },
    [
      comments,
      commentsById,
      commentsNextCursor,
      fetchPage,
      jumpBusy,
      loadErrorMessage,
      notFoundMessage,
      pageLimit,
      scrollToComment,
      setComments,
      setCommentsError,
      setCommentsNextCursor,
    ],
  )

  return { jumpBusy, handleJumpToParent }
}
