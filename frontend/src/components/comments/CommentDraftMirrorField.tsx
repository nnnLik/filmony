import {
  forwardRef,
  useCallback,
  useState,
  type KeyboardEventHandler,
  type Ref,
  type TextareaHTMLAttributes,
} from 'react'

import { CommentBodyWithReactionTokens } from './CommentBodyWithReactionTokens'

function assignRef<T>(instance: T | null, ref: Ref<T> | undefined) {
  if (ref == null) return
  if (typeof ref === 'function') {
    ref(instance)
  } else {
    ref.current = instance
  }
}

type MirrorPlaceholderProps = {
  value: string
  placeholder: string
  mirrorTextClassName: string
  /** Класс цвета плейсхолдера (по умолчанию TGUI hint). */
  placeholderClassName: string
}

function MirrorBody({ value, placeholder, mirrorTextClassName, placeholderClassName }: MirrorPlaceholderProps) {
  if (value.length === 0) {
    return <span className={`${placeholderClassName} ${mirrorTextClassName}`}>{placeholder}</span>
  }
  return (
    <CommentBodyWithReactionTokens text={value} className={`whitespace-pre-wrap ${mirrorTextClassName}`} />
  )
}

export type CommentDraftSingleLineInputProps = {
  value: string
  onChange: (value: string) => void
  placeholder: string
  /** Подпись для скринридеров; по умолчанию совпадает с placeholder. */
  ariaLabel?: string
  disabled?: boolean
  maxLength?: number
  wrapperClassName?: string
  inputClassName?: string
  onKeyDown?: KeyboardEventHandler<HTMLInputElement>
}

export const CommentDraftSingleLineInput = forwardRef<HTMLInputElement, CommentDraftSingleLineInputProps>(
  function CommentDraftSingleLineInput(
    {
      value,
      onChange,
      placeholder,
      ariaLabel,
      disabled,
      maxLength,
      wrapperClassName = '',
      inputClassName = '',
      onKeyDown,
    },
    ref,
  ) {
    const [scrollLeft, setScrollLeft] = useState(0)

    const setRefs = useCallback(
      (node: HTMLInputElement | null) => {
        assignRef(node, ref)
      },
      [ref],
    )

    return (
      <div
        className={`group relative min-h-8 min-w-0 flex-1 rounded-lg border border-(--tgui--divider_color) bg-(--tgui--bg_color) focus-within:border-transparent focus-within:ring-2 focus-within:ring-(--tgui--link_color) ${wrapperClassName}`}
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 z-0 overflow-hidden rounded-[inherit] px-2.5 py-1.5"
        >
          <div
            className="inline-block min-h-[1.25rem] whitespace-nowrap text-[13px] leading-normal text-(--tgui--text_color)"
            style={{ transform: `translateX(-${scrollLeft}px)` }}
          >
            <MirrorBody
              value={value}
              placeholder={placeholder}
              mirrorTextClassName="text-[13px] leading-normal"
              placeholderClassName="text-(--tgui--hint_color)"
            />
          </div>
        </div>
        <input
          ref={setRefs}
          type="text"
          value={value}
          disabled={disabled}
          maxLength={maxLength}
          placeholder=""
          aria-label={ariaLabel ?? placeholder}
          onChange={(e) => onChange(e.currentTarget.value)}
          onScroll={(e) => setScrollLeft(e.currentTarget.scrollLeft)}
          onKeyDown={onKeyDown}
          className={`relative z-10 min-h-8 w-full bg-transparent px-2.5 py-1.5 text-[13px] text-transparent caret-(--tgui--text_color) outline-none selection:bg-[color-mix(in_srgb,var(--tgui--link_color)_24%,transparent)] disabled:opacity-50 ${inputClassName}`}
        />
      </div>
    )
  },
)

/** Caret position after edit (from the native change event); needed for @-mention sync before React commits). */
export type CommentDraftChangeMeta = {
  caret: number
}

export type CommentDraftMultilineProps = {
  value: string
  onChange: (value: string, meta?: CommentDraftChangeMeta) => void
  placeholder: string
  ariaLabel?: string
  disabled?: boolean
  maxLength?: number
  wrapperClassName?: string
  textareaClassName?: string
  /** Цвет текста в зеркале (видимый текст и токены реакций). */
  mirrorOverlayTextClassName?: string
  /** Цвет плейсхолдера в зеркале, когда поле пустое. */
  mirrorPlaceholderClassName?: string
  rows?: number
} & Pick<TextareaHTMLAttributes<HTMLTextAreaElement>, 'onKeyDown' | 'onKeyUp' | 'onSelect'>

export const CommentDraftMultiline = forwardRef<HTMLTextAreaElement, CommentDraftMultilineProps>(
  function CommentDraftMultiline(
    {
      value,
      onChange,
      placeholder,
      ariaLabel,
      disabled,
      maxLength,
      wrapperClassName = '',
      textareaClassName = '',
      mirrorOverlayTextClassName = 'text-(--tgui--text_color)',
      mirrorPlaceholderClassName = 'text-(--tgui--hint_color)',
      rows = 4,
      onKeyDown,
      onKeyUp,
      onSelect,
    },
    ref,
  ) {
    const [scrollTop, setScrollTop] = useState(0)

    const setRefs = useCallback(
      (node: HTMLTextAreaElement | null) => {
        assignRef(node, ref)
      },
      [ref],
    )

    return (
      <div
        className={`relative min-h-24 min-w-0 flex-1 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) ${wrapperClassName}`}
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 z-0 overflow-hidden rounded-[inherit] px-3 py-2"
        >
          <div
            className={`break-words whitespace-pre-wrap text-sm leading-normal ${mirrorOverlayTextClassName}`}
            style={{ transform: `translateY(-${scrollTop}px)` }}
          >
            <MirrorBody
              value={value}
              placeholder={placeholder}
              mirrorTextClassName="text-sm leading-normal"
              placeholderClassName={mirrorPlaceholderClassName}
            />
          </div>
        </div>
        <textarea
          ref={setRefs}
          value={value}
          disabled={disabled}
          maxLength={maxLength}
          rows={rows}
          placeholder=""
          aria-label={ariaLabel ?? placeholder}
          onChange={(e) => {
            const t = e.currentTarget
            onChange(t.value, { caret: t.selectionStart ?? t.value.length })
          }}
          onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
          onKeyDown={onKeyDown}
          onKeyUp={onKeyUp}
          onSelect={onSelect}
          className={`relative z-10 min-h-24 w-full resize-y bg-transparent px-3 py-2 text-sm text-transparent caret-(--tgui--text_color) outline-none selection:bg-[color-mix(in_srgb,var(--tgui--link_color)_24%,transparent)] disabled:opacity-50 ${textareaClassName}`}
        />
      </div>
    )
  },
)
