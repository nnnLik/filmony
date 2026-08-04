import { Button, IconButton } from '@telegram-apps/telegram-ui'
import { Paperclip, X } from 'lucide-react'
import { createPortal } from 'react-dom'
import type { ChangeEvent, KeyboardEventHandler, MouseEventHandler, RefObject } from 'react'

import type { WatchedInlinePickerItem } from '../../api/watchedInlinePickerTypes'
import type { SubscriptionListItem } from '../../api/profileTypes'
import { COMMENT_BODY_MAX_LEN } from '../../lib/commentReactionTokens'
import type { InlineMovieCardRefMeta } from '../../lib/inlineMovieCardRefMap'
import type { ActiveMentionQuery } from '../../lib/feedMentionCompose'
import { displayNameFromProfile } from '../../lib/profileDisplay'
import { CommentDraftMultiline, CommentDraftSingleLineInput } from './CommentDraftMirrorField'
import { CommentReactionTokenPicker } from './CommentReactionTokenPicker'
import { CommentSpoilerToggleButton } from './CommentSpoilerToggleButton'
import { MovieCardInlinePickerButton } from './MovieCardInlinePickerButton'
import { FeedOpenableContainedImageThumbnail } from '../feed/FeedOpenableContainedImage'
import { movieCardCommentImageSrc } from '../../lib/movieCardCommentMedia'
import { IconSend } from '../feed/FeedCardIcons'

export type CommentComposeBarMode = 'singleLine' | 'multiline'

type MentionPopoverLayout = {
  top: number
  left: number
  width: number
  maxHeight: number
}

export type CommentComposeBarProps = {
  mode: CommentComposeBarMode
  value: string
  onChange: (value: string, meta?: { caret: number }) => void
  onSubmit: () => void
  submitBusy?: boolean
  disabled?: boolean
  charsLeft: number
  submitError?: string | null
  placeholder?: string
  inlineMovieCardRefs?: ReadonlyMap<number, InlineMovieCardRefMeta>
  onKeyDown?: KeyboardEventHandler<HTMLTextAreaElement | HTMLInputElement>
  onKeyUp?: () => void
  onSelect?: () => void
  inputRef?: RefObject<HTMLInputElement | null>
  textareaRef?: RefObject<HTMLTextAreaElement | null>
  onInsertReaction?: (reactionTypeId: number) => void
  onToggleSpoiler?: () => void
  onInsertMovieCard?: (row: WatchedInlinePickerItem) => void
  onMouseDown?: MouseEventHandler
  mentionAnchorRef?: RefObject<HTMLDivElement | null>
  mentionPicker?: ActiveMentionQuery | null
  mentionHighlightIdx?: number
  mentionFiltered?: SubscriptionListItem[]
  mentionPopoverLayout?: MentionPopoverLayout | null
  followingMentionQueryPending?: boolean
  followingMentionQueryError?: boolean
  followingMentionItemsCount?: number
  onPickMention?: (slug: string) => void
  onDismissMention?: () => void
  imageUrl?: string | null
  imageUploadBusy?: boolean
  onPickImage?: () => void
  onClearImage?: () => void
  imageFileInputRef?: RefObject<HTMLInputElement | null>
  onImageFileChange?: (event: ChangeEvent<HTMLInputElement>) => void
  submitDisabled?: boolean
}

export function CommentComposeBar({
  mode,
  value,
  onChange,
  onSubmit,
  submitBusy = false,
  disabled = false,
  charsLeft,
  submitError = null,
  placeholder = 'Комментарий…',
  inlineMovieCardRefs,
  onKeyDown,
  onKeyUp,
  onSelect,
  inputRef,
  textareaRef,
  onInsertReaction,
  onToggleSpoiler,
  onInsertMovieCard,
  onMouseDown,
  mentionAnchorRef,
  mentionPicker = null,
  mentionHighlightIdx = 0,
  mentionFiltered = [],
  mentionPopoverLayout = null,
  followingMentionQueryPending = false,
  followingMentionQueryError = false,
  followingMentionItemsCount = 0,
  onPickMention,
  onDismissMention,
  imageUrl = null,
  imageUploadBusy = false,
  onPickImage,
  onClearImage,
  imageFileInputRef,
  onImageFileChange,
  submitDisabled,
}: CommentComposeBarProps) {
  const controlsDisabled = disabled || submitBusy || imageUploadBusy
  const canInsert = value.length < COMMENT_BODY_MAX_LEN
  const defaultSubmitDisabled =
    submitDisabled ?? (value.trim() === '' && (imageUrl ?? '').trim() === '')

  if (mode === 'singleLine') {
    return (
      <div className="flex min-w-0 flex-col gap-1" onMouseDown={onMouseDown}>
        <div className="relative z-10 flex min-w-0 items-stretch gap-1.5">
          <CommentDraftSingleLineInput
            ref={inputRef}
            value={value}
            onChange={onChange}
            disabled={controlsDisabled}
            maxLength={COMMENT_BODY_MAX_LEN}
            placeholder={placeholder}
            ariaLabel="Текст комментария"
            inlineMovieCardRefs={inlineMovieCardRefs}
            onKeyDown={onKeyDown}
          />
          {onInsertReaction != null ? (
            <CommentReactionTokenPicker
              onPickReactionTypeId={onInsertReaction}
              disabled={controlsDisabled}
              allowInsert={canInsert}
            />
          ) : null}
          {onToggleSpoiler != null ? (
            <CommentSpoilerToggleButton
              onToggleSpoiler={onToggleSpoiler}
              disabled={controlsDisabled}
              allowInsert={canInsert}
            />
          ) : null}
          {onInsertMovieCard != null ? (
            <MovieCardInlinePickerButton
              onPick={onInsertMovieCard}
              disabled={controlsDisabled}
              allowInsert={canInsert}
            />
          ) : null}
          <Button
            mode="filled"
            size="s"
            disabled={controlsDisabled || defaultSubmitDisabled}
            type="button"
            className="min-h-8! min-w-8! shrink-0 px-0!"
            onClick={onSubmit}
            aria-label="Отправить комментарий"
          >
            {submitBusy ? '…' : <IconSend className="mx-auto size-4" />}
          </Button>
        </div>
        <div className="flex items-center justify-between gap-2 text-[10px] text-(--tgui--hint_color)">
          <span className="tabular-nums">{charsLeft}</span>
          {submitError != null ? (
            <span className="text-right text-(--tgui--destructive_text_color,#ef4444)">{submitError}</span>
          ) : null}
        </div>
      </div>
    )
  }

  return (
    <div className="mt-3">
      <div className="flex gap-2">
        <div ref={mentionAnchorRef} className="relative min-w-0 flex-1">
          <CommentDraftMultiline
            ref={textareaRef}
            value={value}
            onChange={onChange}
            onKeyDown={onKeyDown}
            onKeyUp={onKeyUp}
            onSelect={onSelect}
            disabled={controlsDisabled}
            rows={4}
            maxLength={COMMENT_BODY_MAX_LEN}
            placeholder={placeholder}
            inlineMovieCardRefs={inlineMovieCardRefs}
          />
          {mentionPicker != null && mentionPopoverLayout != null && onDismissMention != null
            ? createPortal(
                <>
                  <button
                    type="button"
                    tabIndex={-1}
                    aria-hidden
                    className="fixed inset-0 z-200 cursor-default bg-black/0"
                    onClick={onDismissMention}
                  />
                  <div
                    className="filmony-theme fixed z-201 overflow-y-auto rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) py-1 shadow-lg"
                    style={{
                      top: mentionPopoverLayout.top,
                      left: mentionPopoverLayout.left,
                      width: mentionPopoverLayout.width,
                      maxHeight: mentionPopoverLayout.maxHeight,
                    }}
                    role="listbox"
                    aria-label="Упомянуть подписку"
                  >
                    {followingMentionQueryPending ? (
                      <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Загрузка…</p>
                    ) : followingMentionQueryError ? (
                      <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">
                        Не удалось загрузить подписки
                      </p>
                    ) : followingMentionItemsCount === 0 ? (
                      <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">
                        Подпишитесь на пользователей — здесь появятся упоминания.
                      </p>
                    ) : mentionFiltered.length === 0 ? (
                      <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Нет совпадений</p>
                    ) : (
                      mentionFiltered.map((it, idx) => {
                        const label = displayNameFromProfile(it)
                        const selected = idx === mentionHighlightIdx
                        return (
                          <button
                            key={it.id}
                            type="button"
                            role="option"
                            aria-selected={selected}
                            className={`flex w-full flex-col gap-0.5 px-3 py-2 text-left transition active:opacity-90 ${
                              selected
                                ? 'bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_12%,var(--tgui--secondary_bg_color))]'
                                : 'hover:bg-(--tgui--secondary_bg_color)'
                            }`}
                            onMouseDown={(ev) => {
                              ev.preventDefault()
                              onPickMention?.(it.profile_slug)
                            }}
                          >
                            <span className="text-[13px] font-medium text-(--tgui--text_color)">{label}</span>
                            <span className="font-mono text-[11px] text-(--tgui--hint_color)">@{it.profile_slug}</span>
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
        <div className="flex shrink-0 flex-col items-center justify-start gap-1 pt-1">
          {onInsertReaction != null ? (
            <CommentReactionTokenPicker
              onPickReactionTypeId={onInsertReaction}
              disabled={controlsDisabled}
              allowInsert={canInsert}
            />
          ) : null}
          {onToggleSpoiler != null ? (
            <CommentSpoilerToggleButton
              onToggleSpoiler={onToggleSpoiler}
              disabled={controlsDisabled}
              allowInsert={canInsert}
            />
          ) : null}
          {onInsertMovieCard != null ? (
            <MovieCardInlinePickerButton
              onPick={onInsertMovieCard}
              disabled={controlsDisabled}
              allowInsert={canInsert}
            />
          ) : null}
          {onPickImage != null ? (
            <>
              <IconButton
                mode="gray"
                size="s"
                disabled={controlsDisabled}
                onClick={onPickImage}
                aria-label="Добавить картинку"
                title="Добавить картинку"
              >
                <Paperclip className="block size-[18px]" strokeWidth={2} />
              </IconButton>
              {imageFileInputRef != null ? (
                <input
                  ref={imageFileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={onImageFileChange}
                />
              ) : null}
            </>
          ) : null}
        </div>
      </div>
      {imageUrl != null && imageUrl.trim() !== '' && onClearImage != null ? (
        <div className="relative mt-2 overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--card_bg_color)">
          <FeedOpenableContainedImageThumbnail
            src={movieCardCommentImageSrc(imageUrl)}
            wrapperClassName="relative block"
            imgClassName="max-h-[min(50vw,14rem)] w-full object-contain object-center bg-(--tgui--divider_color)"
          />
          <IconButton
            mode="gray"
            size="s"
            className="absolute! right-1 top-1"
            onClick={onClearImage}
            disabled={controlsDisabled}
            aria-label="Убрать картинку"
          >
            <X className="block size-4" strokeWidth={2} />
          </IconButton>
        </div>
      ) : null}
      <div className="mt-1 flex items-center justify-between gap-2">
        <span
          className={`text-xs ${charsLeft < 20 ? 'text-(--tgui--destructive_text_color)' : 'text-(--tgui--hint_color)'}`}
        >
          Осталось: {charsLeft}
        </span>
        <Button
          size="s"
          disabled={controlsDisabled || defaultSubmitDisabled}
          onClick={onSubmit}
          className="motion-safe:transition motion-safe:duration-200 motion-safe:active:scale-[0.97]"
        >
          {submitBusy ? 'Отправка...' : 'Отправить'}
        </Button>
      </div>
    </div>
  )
}
