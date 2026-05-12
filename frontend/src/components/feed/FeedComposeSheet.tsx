import { Button, IconButton } from '@telegram-apps/telegram-ui'
import { Paperclip, X } from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type KeyboardEventHandler,
} from 'react'
import { createPortal } from 'react-dom'

import type { WatchedInlinePickerItem } from '../../api/cardApi'
import { createFeedPost, uploadFeedPostImage } from '../../api/feedPostApi'
import { getMyProfile, getUserSubscriptions } from '../../api/profileApi'
import { ApiError, formatApiDetail, resolveApiUrl } from '../../api/client'
import type { SubscriptionListItem, SubscriptionListResponse } from '../../api/profileTypes'
import { useAuthStatus } from '../../auth/useAuthStatus'
import { CommentBodyWithReactionTokens } from '../comments/CommentBodyWithReactionTokens'
import { CommentDraftMultiline } from '../comments/CommentDraftMirrorField'
import { MovieCardInlinePickerButton } from '../comments/MovieCardInlinePickerButton'
import { CommentReactionTokenPicker } from '../comments/CommentReactionTokenPicker'
import { insertSnippetAtCaret, movieCardRefTokenFromId, reactionTokenFromId } from '../../lib/commentReactionTokens'
import {
  applyMentionPick,
  mentionReplacementFromSlug,
  parseActiveMentionQuery,
  type ActiveMentionQuery,
} from '../../lib/feedMentionCompose'
import { filterFollowingForMentionQuery } from '../../lib/mentionFollowingFilter'
import type { FeedComposeSourceCommentPreview } from '../../compose/feedComposeTypes'
import { globalFeedQueryRootKey } from '../../feed/feedQueryKeys'
import { inlineMovieCardRefMapFromSnippets } from '../../lib/inlineMovieCardRefMap'
import { readMyProfileBundleCache } from '../../lib/myProfileBundleCache'
import { displayNameFromProfile } from '../../lib/profileDisplay'
import { safeHapticSuccess } from '../../lib/safeHaptic'
import { useMentionPopoverLayout } from '../../lib/useMentionPopoverLayout'

const FEED_POST_BODY_MAX = 2000

export type FeedComposeSheetProps = {
  onClose: () => void
  sourceCommentId: number | null
  referencedMovieCardId: number | null
  /** Если комментарий с картинкой — картинка поста фиксирована */
  sourceCommentImageUrl: string | null
  sourceCommentPreview: FeedComposeSourceCommentPreview | null
}

function feedPostImageSrc(url: string): string {
  const u = url.trim()
  if (u.startsWith('http://') || u.startsWith('https://')) return u
  return resolveApiUrl(u.startsWith('/') ? u : `/${u}`)
}

export function FeedComposeSheet({
  onClose,
  sourceCommentId,
  referencedMovieCardId,
  sourceCommentImageUrl,
  sourceCommentPreview,
}: FeedComposeSheetProps) {
  const auth = useAuthStatus()
  const queryClient = useQueryClient()
  const bodyRef = useRef<HTMLTextAreaElement>(null)
  const mentionAnchorRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const mentionOpenRef = useRef(false)

  const [body, setBody] = useState('')
  const [draftInlineCardRefs, setDraftInlineCardRefs] = useState(
    () => new Map<number, { film_title: string; film_year: number | null }>(),
  )
  const [imageUrl, setImageUrl] = useState<string | null>(() => {
    if (
      sourceCommentId != null &&
      sourceCommentImageUrl != null &&
      sourceCommentImageUrl.trim() !== ''
    ) {
      return sourceCommentImageUrl.trim()
    }
    return null
  })
  const [submitBusy, setSubmitBusy] = useState(false)
  const [uploadBusy, setUploadBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mentionPicker, setMentionPicker] = useState<ActiveMentionQuery | null>(null)
  const [mentionHighlightIdx, setMentionHighlightIdx] = useState(0)

  const [subscriptionsUserId, setSubscriptionsUserId] = useState<string | null>(
    () => readMyProfileBundleCache()?.profile.id ?? null,
  )

  useEffect(() => {
    if (auth.kind !== 'ready') return
    const cached = readMyProfileBundleCache()?.profile.id ?? null
    if (cached != null) {
      queueMicrotask(() => {
        setSubscriptionsUserId(cached)
      })
      return
    }
    let alive = true
    void getMyProfile().then(
      (p) => {
        if (alive) {
          queueMicrotask(() => {
            setSubscriptionsUserId(p.id)
          })
        }
      },
      () => {
        void 0
      },
    )
    return () => {
      alive = false
    }
  }, [auth.kind])

  const followingQuery = useQuery<SubscriptionListResponse, Error>({
    queryKey: ['userSubscriptions', subscriptionsUserId, 'following'],
    queryFn: () => getUserSubscriptions(subscriptionsUserId as string, 'following'),
    enabled: subscriptionsUserId != null,
    staleTime: 60_000,
  })

  const followingItems = useMemo((): SubscriptionListItem[] => {
    const raw = followingQuery.data?.items
    return Array.isArray(raw) ? raw : []
  }, [followingQuery.data])

  const mentionFiltered = useMemo((): SubscriptionListItem[] => {
    if (mentionPicker == null) return []
    return filterFollowingForMentionQuery(followingItems, mentionPicker.query)
  }, [followingItems, mentionPicker])

  useEffect(() => {
    mentionOpenRef.current = mentionPicker != null
  }, [mentionPicker])

  const mentionHighlightSafe = useMemo(() => {
    if (mentionFiltered.length === 0) return 0
    return Math.min(mentionHighlightIdx, mentionFiltered.length - 1)
  }, [mentionFiltered.length, mentionHighlightIdx])

  const mentionPopoverLayout = useMentionPopoverLayout(mentionPicker != null, mentionAnchorRef)

  const syncMentionFromValue = useCallback((value: string, caretOverride?: number | null) => {
    const el = bodyRef.current
    const caret =
      caretOverride != null
        ? Math.min(Math.max(0, caretOverride), value.length)
        : Math.min(el?.selectionStart ?? value.length, value.length)
    const active = parseActiveMentionQuery(value, caret)
    if (active == null) {
      setMentionPicker(null)
      setMentionHighlightIdx(0)
      return
    }
    setMentionPicker(active)
    setMentionHighlightIdx(0)
  }, [])

  const fromComment = sourceCommentId != null
  const allowImageUpload = !fromComment
  const charsLeft = FEED_POST_BODY_MAX - body.length

  const hasPostImage = (imageUrl ?? '').trim() !== ''

  const canSubmit = useMemo(() => {
    if (hasPostImage) return true
    return body.trim() !== ''
  }, [body, hasPostImage])

  const pickMentionSlug = useCallback(
    (slug: string) => {
      const el = bodyRef.current
      if (mentionPicker == null || el == null) return
      const endCaret = mentionPicker.atIndex + 1 + mentionPicker.query.length
      const caret = Math.min(endCaret, body.length)
      const token = mentionReplacementFromSlug(slug)
      const res = applyMentionPick(body, caret, mentionPicker.atIndex, token, FEED_POST_BODY_MAX)
      if (res == null) return
      setBody(res.nextValue)
      setMentionPicker(null)
      setMentionHighlightIdx(0)
      queueMicrotask(() => {
        el.focus()
        el.setSelectionRange(res.caret, res.caret)
      })
    },
    [body, mentionPicker],
  )

  const insertReactionToken = useCallback(
    (reactionTypeId: number) => {
      setMentionPicker(null)
      const token = reactionTokenFromId(reactionTypeId)
      const el = bodyRef.current
      const inserted = insertSnippetAtCaret(
        body,
        el?.selectionStart ?? null,
        el?.selectionEnd ?? null,
        token,
        FEED_POST_BODY_MAX,
      )
      if (inserted == null) return
      setBody(inserted.nextValue)
      const caret = inserted.caret
      queueMicrotask(() => {
        el?.focus()
        el?.setSelectionRange(caret, caret)
      })
    },
    [body],
  )

  const insertMovieCardInline = useCallback((row: WatchedInlinePickerItem) => {
    setMentionPicker(null)
    const token = movieCardRefTokenFromId(row.movie_card_id)
    const el = bodyRef.current
    const inserted = insertSnippetAtCaret(
      body,
      el?.selectionStart ?? null,
      el?.selectionEnd ?? null,
      token,
      FEED_POST_BODY_MAX,
    )
    if (inserted == null) return
    setBody(inserted.nextValue)
    setDraftInlineCardRefs((prev) => {
      const next = new Map(prev)
      next.set(row.movie_card_id, { film_title: row.film_title, film_year: row.film_year })
      return next
    })
    const caret = inserted.caret
    queueMicrotask(() => {
      el?.focus()
      el?.setSelectionRange(caret, caret)
    })
  }, [body])

  const handleBodyChange = useCallback(
    (v: string, meta?: { caret: number }) => {
      const next = v.slice(0, FEED_POST_BODY_MAX)
      setBody(next)
      const caret = meta?.caret ?? next.length
      queueMicrotask(() => syncMentionFromValue(next, caret))
    },
    [syncMentionFromValue],
  )

  const handleDraftKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = useCallback(
    (e) => {
      if (mentionPicker == null) return
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setMentionHighlightIdx((i) => {
          const max = Math.max(0, mentionFiltered.length - 1)
          return Math.min(max, i + 1)
        })
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setMentionHighlightIdx((i) => Math.max(0, i - 1))
      } else if (e.key === 'Enter' && mentionFiltered.length > 0) {
        e.preventDefault()
        const row = mentionFiltered[mentionHighlightSafe] ?? mentionFiltered[0]
        if (row != null) {
          pickMentionSlug(row.profile_slug)
        }
      }
    },
    [mentionFiltered, mentionHighlightSafe, mentionPicker, pickMentionSlug],
  )

  const handlePickFile = useCallback(() => {
    if (!allowImageUpload) return
    fileInputRef.current?.click()
  }, [allowImageUpload])

  const onFileChange = useCallback(
    async (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      e.target.value = ''
      if (file == null) return
      if (!file.type.startsWith('image/')) {
        setError('Выберите изображение')
        return
      }
      setUploadBusy(true)
      setError(null)
      try {
        const url = await uploadFeedPostImage(file)
        setImageUrl(url)
      } catch (err) {
        setError(err instanceof ApiError ? formatApiDetail(err.detail) : 'Не удалось загрузить файл')
      } finally {
        setUploadBusy(false)
      }
    },
    [],
  )

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mentionOpenRef.current) {
        e.preventDefault()
        setMentionPicker(null)
        setMentionHighlightIdx(0)
        return
      }
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const handleSubmit = useCallback(async () => {
    if (!canSubmit || submitBusy) return
    if (auth.kind !== 'ready') return
    setSubmitBusy(true)
    setError(null)
    try {
      await createFeedPost({
        body: body.trim(),
        image_url: imageUrl?.trim() === '' || imageUrl == null ? null : imageUrl.trim(),
        referenced_movie_card_id: referencedMovieCardId,
        source_comment_id: sourceCommentId,
      })
      safeHapticSuccess()
      await queryClient.invalidateQueries({ queryKey: globalFeedQueryRootKey })
      setDraftInlineCardRefs(new Map())
      onClose()
    } catch (err) {
      setError(err instanceof ApiError ? formatApiDetail(err.detail) : 'Не удалось отправить')
    } finally {
      setSubmitBusy(false)
    }
  }, [
    auth.kind,
    body,
    canSubmit,
    imageUrl,
    onClose,
    queryClient,
    referencedMovieCardId,
    sourceCommentId,
    submitBusy,
  ])

  if (typeof document === 'undefined') {
    return null
  }

  return createPortal(
    /* Портал вне #root — без .filmony-theme TGUI не видит палитру (кнопка «Отправить», хинты). */
    <div
      className="filmony-theme fixed inset-0 z-50 flex flex-col justify-end text-(--tgui--text_color) pointer-events-auto"
      aria-hidden={false}
    >
      <button
        type="button"
        className="absolute inset-0 bg-[color-mix(in_srgb,var(--filmony-ink,#06090d)_72%,transparent)] opacity-100 transition-opacity duration-200"
        tabIndex={0}
        aria-label="Закрыть"
        onClick={onClose}
      />
      <div
        className="relative z-10 isolate mx-auto flex max-h-[min(72dvh,22rem)] w-full max-w-md flex-col rounded-t-[22px] border border-(--tgui--divider_color) bg-(--tgui--tertiary_bg_color) shadow-[0_-16px_48px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.06)] motion-safe:animate-[filmony-detail-fade-in_0.2s_ease-out_both] ring-1 ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_14%,transparent)]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="feed-compose-title"
      >
        <div className="flex shrink-0 items-center justify-between gap-2 border-b border-[color-mix(in_srgb,var(--tgui--divider_color)_75%,transparent)] px-3 py-2.5">
          <h2 id="feed-compose-title" className="min-w-0 flex-1 truncate text-[16px] font-semibold tracking-tight text-(--tgui--text_color)">
            Пост
          </h2>
          <IconButton mode="gray" size="s" onClick={onClose} aria-label="Закрыть">
            <X className="block size-5" strokeWidth={2} />
          </IconButton>
        </div>

        <div className="flex min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto bg-(--tgui--bg_color) px-3 py-3">
          {fromComment && sourceCommentPreview != null ? (
            <div className="rounded-xl border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_18%,var(--tgui--divider_color))] bg-(--tgui--secondary_bg_color) px-3 py-2.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-(--tgui--hint_color)">Из комментария</p>
              <p className="mt-0.5 text-[13px] font-medium text-(--tgui--text_color)">{sourceCommentPreview.authorLabel}</p>
              {sourceCommentPreview.text.trim() !== '' ? (
                <p className="mt-2 text-sm leading-relaxed text-(--tgui--text_color)">
                  <CommentBodyWithReactionTokens
                    text={sourceCommentPreview.text}
                    className="whitespace-pre-wrap"
                    inlineMovieCardRefs={inlineMovieCardRefMapFromSnippets(sourceCommentPreview.referencedMovieCards)}
                    referencedMentions={sourceCommentPreview.referencedMentions}
                  />
                </p>
              ) : sourceCommentImageUrl != null && sourceCommentImageUrl.trim() !== '' ? (
                <p className="mt-2 text-[12px] text-(--tgui--hint_color)">
                  В комментарии только фото — оно переносится в пост ниже; здесь напишите подпись к посту (по желанию).
                </p>
              ) : null}
            </div>
          ) : null}

          {fromComment ? (
            <p className="text-[12px] leading-snug text-(--tgui--hint_color)">
              Ниже — только текст поста в ленту; он не смешивается с комментарием выше.
            </p>
          ) : null}

          <div ref={mentionAnchorRef} className="relative">
            <CommentDraftMultiline
              ref={bodyRef}
              value={body}
              onChange={handleBodyChange}
              onKeyUp={() => {
                const el = bodyRef.current
                if (el == null) return
                syncMentionFromValue(
                  el.value.slice(0, FEED_POST_BODY_MAX),
                  el.selectionStart ?? el.value.length,
                )
              }}
              onSelect={() => {
                const el = bodyRef.current
                if (el == null) return
                syncMentionFromValue(
                  el.value.slice(0, FEED_POST_BODY_MAX),
                  el.selectionStart ?? el.value.length,
                )
              }}
              onKeyDown={handleDraftKeyDown}
              placeholder="Напишите пост…"
              ariaLabel="Текст поста"
              disabled={submitBusy || uploadBusy}
              maxLength={FEED_POST_BODY_MAX}
              rows={3}
              mirrorPlaceholderClassName="text-(--tgui--hint_color)"
              mirrorOverlayTextClassName="text-(--tgui--text_color)"
              wrapperClassName="min-h-[5.5rem] !rounded-xl !border !border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_22%,var(--tgui--divider_color))] !bg-(--tgui--card_bg_color) shadow-[inset_0_1px_0_rgba(255,255,255,0.055),inset_0_-1px_0_rgba(0,0,0,0.2)] focus-within:!border-(--tgui--link_color) focus-within:ring-2 focus-within:ring-[color-mix(in_srgb,var(--tgui--link_color)_38%,transparent)]"
              textareaClassName="text-sm caret-(--tgui--link_color) selection:bg-[color-mix(in_srgb,var(--tgui--link_color)_28%,transparent)]"
              inlineMovieCardRefs={draftInlineCardRefs}
            />

            {mentionPicker != null && mentionPopoverLayout != null
              ? createPortal(
                  <>
                    <button
                      type="button"
                      tabIndex={-1}
                      aria-hidden
                      className="fixed inset-0 z-200 cursor-default bg-black/0"
                      onClick={() => {
                        setMentionPicker(null)
                        setMentionHighlightIdx(0)
                      }}
                    />
                    <div
                      className="filmony-theme fixed z-201 overflow-y-auto rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color) py-1 shadow-[0_10px_36px_rgba(0,0,0,0.45)] ring-1 ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_10%,transparent)]"
                      style={{
                        top: mentionPopoverLayout.top,
                        left: mentionPopoverLayout.left,
                        width: mentionPopoverLayout.width,
                        maxHeight: mentionPopoverLayout.maxHeight,
                      }}
                      role="listbox"
                      aria-label="Упомянуть подписку"
                    >
                      {followingQuery.isPending ? (
                        <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Загрузка…</p>
                      ) : followingQuery.isError ? (
                        <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Не удалось загрузить подписки</p>
                      ) : followingItems.length === 0 ? (
                        <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">
                          Подпишитесь на пользователей — здесь появятся упоминания.
                        </p>
                      ) : mentionFiltered.length === 0 ? (
                        <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Нет совпадений</p>
                      ) : (
                        mentionFiltered.map((it, idx) => {
                          const label = displayNameFromProfile(it)
                          const selected = idx === mentionHighlightSafe
                          return (
                            <button
                              key={it.id}
                              type="button"
                              role="option"
                              aria-selected={selected}
                              className={`flex w-full flex-col gap-0.5 px-3 py-2 text-left transition ${
                                selected
                                  ? 'bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_12%,var(--tgui--secondary_bg_color))]'
                                  : 'hover:bg-[color-mix(in_srgb,var(--tgui--hint_color)_08%,var(--tgui--secondary_bg_color))] active:bg-[color-mix(in_srgb,var(--tgui--hint_color)_12%,var(--tgui--secondary_bg_color))]'
                              }`}
                              onMouseDown={(ev) => {
                                ev.preventDefault()
                                pickMentionSlug(it.profile_slug)
                              }}
                            >
                              <span className="text-[13px] font-medium text-(--tgui--text_color)">{label}</span>
                              <span className="font-mono text-[11px] text-(--tgui--accent_text_color)">@{it.profile_slug}</span>
                            </button>
                          )
                        })
                      )}
                    </div>
                  </>,
                  document.body,
                )
              : null}
          </div>

          <div className="flex items-center justify-between gap-2 text-[12px] text-(--tgui--hint_color)">
            <span className="tabular-nums font-medium text-(--tgui--secondary_hint_color)">{charsLeft}</span>
            <div className="flex shrink-0 items-center gap-1">
              <CommentReactionTokenPicker
                onPickReactionTypeId={insertReactionToken}
                disabled={submitBusy || uploadBusy}
                allowInsert={body.length < FEED_POST_BODY_MAX}
              />
              <MovieCardInlinePickerButton
                onPick={insertMovieCardInline}
                disabled={submitBusy || uploadBusy}
                allowInsert={body.length < FEED_POST_BODY_MAX}
              />
              <IconButton
                mode="gray"
                size="s"
                disabled={submitBusy || uploadBusy || !allowImageUpload}
                onClick={handlePickFile}
                aria-label="Добавить картинку"
                title={allowImageUpload ? 'Добавить картинку' : 'Картинка задаётся только из комментария'}
              >
                <Paperclip className="block size-[18px]" strokeWidth={2} />
              </IconButton>
            </div>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => void onFileChange(e)}
          />

          {imageUrl != null && imageUrl.trim() !== '' ? (
            <div className="relative mt-0.5 overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--card_bg_color)">
              <img
                src={feedPostImageSrc(imageUrl)}
                alt=""
                className="max-h-[min(50vw,14rem)] w-full object-cover object-center"
              />
              <IconButton
                mode="gray"
                size="s"
                className="absolute! right-1 top-1"
                onClick={() => setImageUrl(null)}
                disabled={submitBusy || uploadBusy || !allowImageUpload}
                aria-label="Убрать картинку"
              >
                <X className="block size-4" strokeWidth={2} />
              </IconButton>
            </div>
          ) : null}

          {error != null ? (
            <p className="rounded-xl border border-red-500/50 bg-red-950/40 px-3 py-2 text-[13px] text-red-200">
              {error}
            </p>
          ) : null}
        </div>

        <div className="shrink-0 border-t border-[color-mix(in_srgb,var(--tgui--divider_color)_80%,transparent)] bg-(--tgui--secondary_bg_color) px-3 py-3 pb-[max(12px,calc(10px+env(safe-area-inset-bottom)))] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
          <Button
            stretched
            mode="filled"
            size="l"
            className="font-semibold! shadow-[0_1px_0_rgba(255,255,255,0.12)]!"
            disabled={!canSubmit || submitBusy || uploadBusy || auth.kind !== 'ready'}
            onClick={() => void handleSubmit()}
          >
            {uploadBusy ? 'Загрузка…' : submitBusy ? 'Отправка…' : 'Отправить'}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
