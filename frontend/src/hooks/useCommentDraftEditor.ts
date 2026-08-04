import {
  useCallback,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type KeyboardEventHandler,
  type RefObject,
  type SetStateAction,
} from 'react'

import type { WatchedInlinePickerItem } from '../api/watchedInlinePickerTypes'
import type { SubscriptionListItem } from '../api/profileTypes'
import {
  COMMENT_BODY_MAX_LEN,
  insertSnippetAtCaret,
  movieCardRefTokenFromId,
  reactionTokenFromId,
} from '../lib/commentReactionTokens'
import {
  applyMentionPick,
  mentionReplacementFromSlug,
  parseActiveMentionQuery,
  type ActiveMentionQuery,
} from '../lib/feedMentionCompose'
import { filterFollowingForMentionQuery } from '../lib/mentionFollowingFilter'
import type { InlineMovieCardRefMeta } from '../lib/inlineMovieCardRefMap'
import { toggleSpoilerAtSelection } from '../lib/spoilerTokens'
import { useMentionPopoverLayout } from '../lib/useMentionPopoverLayout'

type UseCommentDraftEditorArgs = {
  followingMentionItems: SubscriptionListItem[]
  disabled?: boolean
}

type UseCommentDraftEditorResult = {
  commentText: string
  setCommentText: (value: string) => void
  commentDraftInlineCardRefs: Map<number, InlineMovieCardRefMeta>
  setCommentDraftInlineCardRefs: Dispatch<SetStateAction<Map<number, InlineMovieCardRefMeta>>>
  commentTextAreaRef: RefObject<HTMLTextAreaElement | null>
  commentMentionAnchorRef: RefObject<HTMLDivElement | null>
  commentMentionPicker: ActiveMentionQuery | null
  commentMentionHighlightIdx: number
  commentMentionFiltered: SubscriptionListItem[]
  commentMentionPopoverLayout: ReturnType<typeof useMentionPopoverLayout>
  charsLeft: number
  handleCommentTextChange: (value: string, meta?: { caret: number }) => void
  handleCommentDraftKeyDown: KeyboardEventHandler<HTMLTextAreaElement>
  syncCommentMentionFromValue: (value: string, caretOverride?: number | null) => void
  pickCommentMention: (slug: string) => void
  dismissCommentMention: () => void
  insertReactionIntoComment: (reactionTypeId: number) => void
  insertMovieCardIntoComment: (row: WatchedInlinePickerItem) => void
  toggleSpoilerInComment: () => void
  resetDraft: () => void
}

export function useCommentDraftEditor({
  followingMentionItems,
  disabled = false,
}: UseCommentDraftEditorArgs): UseCommentDraftEditorResult {
  const [commentText, setCommentText] = useState('')
  const [commentDraftInlineCardRefs, setCommentDraftInlineCardRefs] = useState<
    Map<number, InlineMovieCardRefMeta>
  >(() => new Map())
  const [commentMentionPicker, setCommentMentionPicker] = useState<ActiveMentionQuery | null>(null)
  const [commentMentionHighlightIdx, setCommentMentionHighlightIdx] = useState(0)
  const commentTextAreaRef = useRef<HTMLTextAreaElement>(null)
  const commentMentionAnchorRef = useRef<HTMLDivElement>(null)

  const commentMentionFiltered = useMemo(
    () =>
      commentMentionPicker != null
        ? filterFollowingForMentionQuery(followingMentionItems, commentMentionPicker.query)
        : [],
    [commentMentionPicker, followingMentionItems],
  )

  const commentMentionHighlightSafe = useMemo(() => {
    if (commentMentionFiltered.length === 0) return 0
    return Math.min(commentMentionHighlightIdx, commentMentionFiltered.length - 1)
  }, [commentMentionFiltered.length, commentMentionHighlightIdx])

  const commentMentionPopoverLayout = useMentionPopoverLayout(
    commentMentionPicker != null,
    commentMentionAnchorRef,
  )

  const dismissCommentMention = useCallback(() => {
    setCommentMentionPicker(null)
    setCommentMentionHighlightIdx(0)
  }, [])

  const syncCommentMentionFromValue = useCallback((value: string, caretOverride?: number | null) => {
    const el = commentTextAreaRef.current
    const caret =
      caretOverride != null
        ? Math.min(Math.max(0, caretOverride), value.length)
        : Math.min(el?.selectionStart ?? value.length, value.length)
    const active = parseActiveMentionQuery(value, caret)
    if (active == null) {
      dismissCommentMention()
      return
    }
    setCommentMentionPicker(active)
    setCommentMentionHighlightIdx(0)
  }, [dismissCommentMention])

  const handleCommentTextChange = useCallback(
    (value: string, meta?: { caret: number }) => {
      const next = value.slice(0, COMMENT_BODY_MAX_LEN)
      setCommentText(next)
      const caret = meta?.caret ?? next.length
      queueMicrotask(() => syncCommentMentionFromValue(next, caret))
    },
    [syncCommentMentionFromValue],
  )

  const pickCommentMention = useCallback(
    (slug: string) => {
      const el = commentTextAreaRef.current
      if (commentMentionPicker == null || el == null) return
      const endCaret = commentMentionPicker.atIndex + 1 + commentMentionPicker.query.length
      const caret = Math.min(endCaret, commentText.length)
      const token = mentionReplacementFromSlug(slug)
      const res = applyMentionPick(commentText, caret, commentMentionPicker.atIndex, token, COMMENT_BODY_MAX_LEN)
      if (res == null) return
      setCommentText(res.nextValue)
      dismissCommentMention()
      queueMicrotask(() => {
        el.focus()
        el.setSelectionRange(res.caret, res.caret)
      })
    },
    [commentMentionPicker, commentText, dismissCommentMention],
  )

  const handleCommentDraftKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = useCallback(
    (event) => {
      if (commentMentionPicker == null || disabled) return
      if (event.key === 'ArrowDown') {
        event.preventDefault()
        setCommentMentionHighlightIdx((index) => {
          const max = Math.max(0, commentMentionFiltered.length - 1)
          return Math.min(max, index + 1)
        })
      } else if (event.key === 'ArrowUp') {
        event.preventDefault()
        setCommentMentionHighlightIdx((index) => Math.max(0, index - 1))
      } else if (event.key === 'Enter' && commentMentionFiltered.length > 0) {
        event.preventDefault()
        const row = commentMentionFiltered[commentMentionHighlightSafe] ?? commentMentionFiltered[0]
        if (row != null) {
          pickCommentMention(row.profile_slug)
        }
      }
    },
    [commentMentionFiltered, commentMentionHighlightSafe, commentMentionPicker, disabled, pickCommentMention],
  )

  const insertReactionIntoComment = useCallback(
    (reactionTypeId: number) => {
      dismissCommentMention()
      const token = reactionTokenFromId(reactionTypeId)
      const el = commentTextAreaRef.current
      const inserted = insertSnippetAtCaret(
        commentText,
        el?.selectionStart ?? null,
        el?.selectionEnd ?? null,
        token,
        COMMENT_BODY_MAX_LEN,
      )
      if (inserted == null) return
      setCommentText(inserted.nextValue)
      const caret = inserted.caret
      queueMicrotask(() => {
        el?.focus()
        el?.setSelectionRange(caret, caret)
      })
    },
    [commentText, dismissCommentMention],
  )

  const insertMovieCardIntoComment = useCallback(
    (row: WatchedInlinePickerItem) => {
      dismissCommentMention()
      const token = movieCardRefTokenFromId(row.movie_card_id)
      const el = commentTextAreaRef.current
      const inserted = insertSnippetAtCaret(
        commentText,
        el?.selectionStart ?? null,
        el?.selectionEnd ?? null,
        token,
        COMMENT_BODY_MAX_LEN,
      )
      if (inserted == null) return
      setCommentText(inserted.nextValue)
      setCommentDraftInlineCardRefs((prev) => {
        const next = new Map(prev)
        next.set(row.movie_card_id, { film_title: row.film_title, film_year: row.film_year })
        return next
      })
      const caret = inserted.caret
      queueMicrotask(() => {
        el?.focus()
        el?.setSelectionRange(caret, caret)
      })
    },
    [commentText, dismissCommentMention],
  )

  const toggleSpoilerInComment = useCallback(() => {
    dismissCommentMention()
    const el = commentTextAreaRef.current
    const toggled = toggleSpoilerAtSelection(
      commentText,
      el?.selectionStart ?? null,
      el?.selectionEnd ?? null,
      COMMENT_BODY_MAX_LEN,
    )
    if (toggled == null) return
    setCommentText(toggled.nextValue)
    const caret = toggled.caret
    queueMicrotask(() => {
      el?.focus()
      el?.setSelectionRange(caret, caret)
    })
  }, [commentText, dismissCommentMention])

  const resetDraft = useCallback(() => {
    setCommentText('')
    setCommentDraftInlineCardRefs(new Map())
    dismissCommentMention()
  }, [dismissCommentMention])

  const charsLeft = COMMENT_BODY_MAX_LEN - commentText.length

  return {
    commentText,
    setCommentText,
    commentDraftInlineCardRefs,
    setCommentDraftInlineCardRefs,
    commentTextAreaRef,
    commentMentionAnchorRef,
    commentMentionPicker,
    commentMentionHighlightIdx: commentMentionHighlightSafe,
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
  }
}
