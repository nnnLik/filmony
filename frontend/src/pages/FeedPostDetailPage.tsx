import { IconButton } from '@telegram-apps/telegram-ui'
import { ArrowLeft } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router'

import {
  createFeedPostComment,
  deleteFeedPostComment,
  getFeedPostById,
  getFeedPostComments,
  updateFeedPostComment,
} from '../api/feedPostApi'
import { getMyProfile, getUserSubscriptions } from '../api/profileApi'
import { ApiError, formatApiDetail } from '../api/client'
import type { FeedPostInFeed } from '../api/feedInFeedTypes'
import type { FeedPostComment } from '../api/profileTypes'
import { CommentThreadSection } from '../components/comments/CommentThreadSection'
import { MentionProfileLookupProvider } from '../context/MentionProfileLookupProvider'
import { COMMENT_BODY_MAX_LEN } from '../lib/commentReactionTokens'
import { FeedPostCard } from '../components/feed/FeedPostCard'
import {
  authorLikeToMentionRow,
  mentionProfileKeyFromSlug,
  type MentionProfileRowInput,
} from '../lib/mentionProfileLookupUtils'
import { subscriptionToMentionRow } from '../lib/subscriptionToMentionRow'
import { markGlobalFeedPostDetailOpened } from '../lib/globalFeedViewedIds'
import { readMyProfileBundleCache } from '../lib/myProfileBundleCache'
import { safeHapticSuccess } from '../lib/safeHaptic'
import { useTasteQuizKnowledgeOfUsers } from '../hooks/useTasteQuizKnowledgeOfUsers'
import { useRatingStreaksOfUsers } from '../hooks/useRatingStreaksOfUsers'
import { useCommentScrollHighlight } from '../hooks/useCommentScrollHighlight'
import { usePaginatedComments } from '../hooks/usePaginatedComments'
import { useCommentJumpToParent } from '../hooks/useCommentJumpToParent'
import { useCommentDraftEditor } from '../hooks/useCommentDraftEditor'

export function FeedPostDetailPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const params = useParams<{ postId: string }>()
  const parsedPostId = useMemo(() => {
    const n = Number(params.postId)
    return Number.isInteger(n) && n >= 1 ? n : null
  }, [params.postId])

  const [post, setPost] = useState<FeedPostInFeed | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [viewerId, setViewerId] = useState<string | null>(() => readMyProfileBundleCache()?.profile.id ?? null)
  const [replyTo, setReplyTo] = useState<{ id: number; label: string } | null>(null)
  const [submitBusy, setSubmitBusy] = useState(false)
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null)
  const [editText, setEditText] = useState('')
  const [editBusy, setEditBusy] = useState(false)
  const [deleteCommentBusyId, setDeleteCommentBusyId] = useState<number | null>(null)

  const commentsEnabled = parsedPostId != null && error == null && post != null

  const {
    comments,
    setComments,
    commentsNextCursor,
    setCommentsNextCursor,
    commentsById,
    commentsLoading,
    commentsError,
    setCommentsError,
    loadComments,
  } = usePaginatedComments<FeedPostComment>({
    enabled: commentsEnabled,
    mode: 'page',
    fetchPage: useCallback(
      ({ cursor, limit }) => {
        if (parsedPostId == null) {
          return Promise.reject(new Error('missing post id'))
        }
        return getFeedPostComments(parsedPostId, { cursor, limit })
      },
      [parsedPostId],
    ),
  })

  const { highlightCommentId, setCommentRef, scrollToComment } = useCommentScrollHighlight()

  const { jumpBusy, handleJumpToParent } = useCommentJumpToParent({
    comments,
    commentsById,
    commentsNextCursor,
    setComments,
    setCommentsNextCursor,
    setCommentsError,
    fetchPage: useCallback(
      ({ cursor, limit }) => {
        if (parsedPostId == null) {
          return Promise.reject(new Error('missing post id'))
        }
        return getFeedPostComments(parsedPostId, { cursor, limit })
      },
      [parsedPostId],
    ),
    scrollToComment,
  })

  const followingForMentionsQuery = useQuery({
    queryKey: ['userSubscriptions', viewerId, 'following'],
    queryFn: () => getUserSubscriptions(viewerId as string, 'following'),
    enabled: viewerId != null,
    staleTime: 60_000,
  })
  const followingMentionItems = useMemo(
    () => followingForMentionsQuery.data?.items ?? [],
    [followingForMentionsQuery.data],
  )

  const {
    commentText,
    commentDraftInlineCardRefs,
    commentTextAreaRef,
    commentMentionAnchorRef,
    commentMentionPicker,
    commentMentionHighlightIdx,
    commentMentionFiltered,
    commentMentionPopoverLayout,
    charsLeft,
    handleCommentTextChange,
    handleCommentDraftKeyDown,
    syncCommentMentionFromValue,
    pickCommentMention,
    dismissCommentMention,
    insertReactionIntoComment,
    insertMovieCardIntoComment,
    toggleSpoilerInComment,
    resetDraft,
  } = useCommentDraftEditor({
    followingMentionItems,
    disabled: submitBusy,
  })

  const tasteQuizOwnerIds = useMemo(() => {
    const ids = new Set<string>()
    if (post != null && viewerId != null && post.user_id !== viewerId) {
      ids.add(post.user_id)
    }
    for (const comment of comments) {
      ids.add(comment.author.id)
    }
    return [...ids]
  }, [comments, post, viewerId])
  const streakUserIds = useMemo(() => {
    const ids = new Set<string>()
    if (post != null) {
      ids.add(post.user_id)
    }
    for (const comment of comments) {
      ids.add(comment.author.id)
    }
    return [...ids]
  }, [comments, post])
  const { knowledgeByOwnerId } = useTasteQuizKnowledgeOfUsers(tasteQuizOwnerIds, {
    enabled: tasteQuizOwnerIds.length > 0,
  })
  const { streakByUserId } = useRatingStreaksOfUsers(streakUserIds, {
    enabled: streakUserIds.length > 0,
  })

  const mentionRowsForPostDetail = useMemo((): MentionProfileRowInput[] => {
    const seen = new Set<string>()
    const out: MentionProfileRowInput[] = []
    const push = (r: MentionProfileRowInput) => {
      const k = mentionProfileKeyFromSlug(r.profile_slug)
      if (k.length === 0 || seen.has(k)) return
      seen.add(k)
      out.push(r)
    }
    if (post != null) push(authorLikeToMentionRow(post.author))
    for (const c of comments) push(authorLikeToMentionRow(c.author))
    for (const it of followingMentionItems) push(subscriptionToMentionRow(it))
    return out
  }, [comments, followingMentionItems, post])

  useEffect(() => {
    if (viewerId != null) return
    let alive = true
    void (async () => {
      try {
        const profile = await getMyProfile()
        if (!alive) return
        setViewerId(profile.id)
      } catch {
        void 0
      }
    })()
    return () => {
      alive = false
    }
  }, [viewerId])

  useEffect(() => {
    if (parsedPostId == null) return
    let alive = true
    void (async () => {
      setLoading(true)
      setError(null)
      try {
        const item = await getFeedPostById(parsedPostId)
        if (!alive) return
        setPost(item)
      } catch (e) {
        if (!alive) return
        if (e instanceof ApiError) setError(formatApiDetail(e.detail))
        else setError('Не удалось загрузить пост')
      } finally {
        if (alive) setLoading(false)
      }
    })()
    return () => {
      alive = false
    }
  }, [parsedPostId])

  useEffect(() => {
    if (parsedPostId == null || post == null) return
    markGlobalFeedPostDetailOpened(parsedPostId)
  }, [parsedPostId, post])

  async function handleCreateComment() {
    if (parsedPostId == null || submitBusy) return
    const text = commentText.trim()
    if (text === '') return
    setSubmitBusy(true)
    setCommentsError(null)
    try {
      await createFeedPostComment(parsedPostId, {
        text,
        parent_comment_id: replyTo?.id ?? null,
      })
      await loadComments(false)
      try {
        const fresh = await getFeedPostById(parsedPostId)
        setPost(fresh)
      } catch {
        void 0
      }
      resetDraft()
      setReplyTo(null)
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) setCommentsError(formatApiDetail(e.detail))
      else setCommentsError('Не удалось отправить комментарий')
    } finally {
      setSubmitBusy(false)
    }
  }

  function handleCancelEdit() {
    setEditingCommentId(null)
    setEditText('')
  }

  async function handleSaveEdit(commentId: number) {
    if (parsedPostId == null || editBusy) return
    const text = editText.trim()
    if (text === '') return
    setEditBusy(true)
    setCommentsError(null)
    try {
      const updated = await updateFeedPostComment(parsedPostId, commentId, { text })
      setComments((prev) => prev.map((c) => (c.id === commentId ? updated : c)))
      handleCancelEdit()
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) setCommentsError(formatApiDetail(e.detail))
      else setCommentsError('Не удалось сохранить комментарий')
    } finally {
      setEditBusy(false)
    }
  }

  async function handleDeleteComment(commentId: number) {
    if (parsedPostId == null || deleteCommentBusyId != null) return
    const confirmed = window.confirm('Удалить комментарий? Ответы на него тоже будут удалены.')
    if (!confirmed) return
    setDeleteCommentBusyId(commentId)
    setCommentsError(null)
    try {
      await deleteFeedPostComment(parsedPostId, commentId)
      if (editingCommentId === commentId) handleCancelEdit()
      await loadComments(false)
      try {
        const fresh = await getFeedPostById(parsedPostId)
        setPost(fresh)
      } catch {
        void 0
      }
      safeHapticSuccess()
    } catch (e) {
      if (e instanceof ApiError) setCommentsError(formatApiDetail(e.detail))
      else setCommentsError('Не удалось удалить комментарий')
    } finally {
      setDeleteCommentBusyId(null)
    }
  }

  const invalidPostId = parsedPostId == null
  const showLoading = !invalidPostId && loading

  const handleNavigateBack = useCallback(() => {
    const st = location.state as { fromFeed?: boolean } | undefined
    if (st?.fromFeed || location.key === 'default') {
      void navigate('/')
      return
    }
    void navigate(-1)
  }, [location.key, location.state, navigate])

  const handlePostDeleted = useCallback(() => {
    handleNavigateBack()
  }, [handleNavigateBack])

  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) text-(--tgui--text_color)">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--bg_color)_92%,transparent)] px-3 py-2 backdrop-blur-md">
        <IconButton
          size="s"
          mode="gray"
          aria-label="Назад"
          onClick={handleNavigateBack}
        >
          <ArrowLeft className="relative z-1 block size-[18px]" strokeWidth={1.75} aria-hidden />
        </IconButton>
        <span className="truncate text-sm font-medium text-(--tgui--hint_color)">Пост</span>
      </header>

      <main className="mx-auto max-w-md px-3 pb-10 pt-3 sm:px-4">
        {invalidPostId ? (
          <p className="filmony-text-panel py-8 text-center text-sm text-(--tgui--destructive_text_color)">
            Некорректный адрес поста
          </p>
        ) : null}

        {showLoading ? (
          <p className="filmony-text-panel py-10 text-center text-sm text-(--tgui--hint_color)">Загрузка…</p>
        ) : null}

        {error != null ? (
          <p className="filmony-text-panel py-8 text-center text-sm text-(--tgui--destructive_text_color)">{error}</p>
        ) : null}

        {!showLoading && post != null ? (
          <MentionProfileLookupProvider value={mentionRowsForPostDetail}>
            <FeedPostCard
              post={post}
              viewerUserId={viewerId}
              linkToDetail={false}
              inlineComments={false}
              onPostUpdated={setPost}
              onPostDeleted={handlePostDeleted}
            />

            <CommentThreadSection
              comments={comments}
              commentsById={commentsById}
              commentsLoading={commentsLoading}
              commentsError={commentsError}
              commentsNextCursor={commentsNextCursor}
              loadComments={loadComments}
              replyTo={replyTo}
              setReplyTo={setReplyTo}
              viewerId={viewerId}
              submitBusy={submitBusy}
              jumpBusy={jumpBusy}
              highlightCommentId={highlightCommentId}
              setCommentRef={setCommentRef}
              handleJumpToParent={handleJumpToParent}
              handleCreateComment={handleCreateComment}
              commentText={commentText}
              onCommentTextChange={handleCommentTextChange}
              onCommentKeyDown={handleCommentDraftKeyDown}
              onCommentKeyUp={() => {
                const el = commentTextAreaRef.current
                if (el == null) return
                syncCommentMentionFromValue(
                  el.value.slice(0, COMMENT_BODY_MAX_LEN),
                  el.selectionStart ?? el.value.length,
                )
              }}
              onCommentSelect={() => {
                const el = commentTextAreaRef.current
                if (el == null) return
                syncCommentMentionFromValue(
                  el.value.slice(0, COMMENT_BODY_MAX_LEN),
                  el.selectionStart ?? el.value.length,
                )
              }}
              commentTextAreaRef={commentTextAreaRef}
              commentDraftInlineCardRefs={commentDraftInlineCardRefs}
              insertReactionIntoComment={insertReactionIntoComment}
              toggleSpoilerInComment={toggleSpoilerInComment}
              insertMovieCardIntoComment={insertMovieCardIntoComment}
              charsLeft={charsLeft}
              commentMentionAnchorRef={commentMentionAnchorRef}
              commentMentionPicker={commentMentionPicker}
              commentMentionHighlightIdx={commentMentionHighlightIdx}
              commentMentionFiltered={commentMentionFiltered}
              commentMentionPopoverLayout={commentMentionPopoverLayout}
              followingMentionItems={followingMentionItems}
              followingMentionQueryPending={followingForMentionsQuery.isPending}
              followingMentionQueryError={followingForMentionsQuery.isError}
              onPickCommentMention={pickCommentMention}
              onDismissCommentMention={dismissCommentMention}
              tasteQuizKnowledgeByAuthor={knowledgeByOwnerId}
              streakByUserId={streakByUserId}
              editingCommentId={editingCommentId}
              editText={editText}
              setEditText={setEditText}
              editBusy={editBusy}
              deleteCommentBusyId={deleteCommentBusyId}
              onStartEditComment={(comment) => {
                setEditingCommentId(comment.id)
                setEditText(comment.text)
              }}
              onCancelEditComment={handleCancelEdit}
              onSaveEditComment={(comment) => void handleSaveEdit(comment.id)}
              onDeleteComment={(commentId) => void handleDeleteComment(commentId)}
              setComments={setComments}
              reactionTargetKind="feed_post_comment"
              sectionClassName="mt-4 rounded-2xl border border-(--tgui--divider_color) bg-[color-mix(in_srgb,var(--tgui--secondary_bg_color)_94%,transparent)] p-3.5 sm:p-4"
            />
          </MentionProfileLookupProvider>
        ) : null}
      </main>
    </div>
  )
}
