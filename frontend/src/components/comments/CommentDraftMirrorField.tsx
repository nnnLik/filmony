import {
  forwardRef,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type KeyboardEventHandler,
  type Ref,
  type RefObject,
  type SyntheticEvent,
  type TextareaHTMLAttributes,
} from 'react'

import { richMirrorCaretPositionInRoot } from '../../lib/commentDraftCaretGeometry'
import type { InlineMovieCardRefMeta } from '../../lib/inlineMovieCardRefMap'
import { CommentBodyWithReactionTokens } from './CommentBodyWithReactionTokens'

function assignRef<T>(instance: T | null, ref: Ref<T> | undefined) {
  if (ref == null) return
  if (typeof ref === 'function') {
    ref(instance)
  } else {
    ref.current = instance
  }
}

type FakeCaret = { left: number; top: number; height: number; caretColor: string }

function useFakeCaretOverlay(
  value: string,
  fieldRef: RefObject<HTMLInputElement | HTMLTextAreaElement | null>,
  scrollMirror: { x: number; y: number },
) {
  const wrapperRef = useRef<HTMLDivElement>(null)
  const mirrorInnerRef = useRef<HTMLDivElement>(null)
  const [measureTick, setMeasureTick] = useState(0)
  const [fakeCaret, setFakeCaret] = useState<FakeCaret | null>(null)

  const bumpMeasure = useCallback(() => {
    setMeasureTick((n) => n + 1)
  }, [])

  useLayoutEffect(() => {
    const wrap = wrapperRef.current
    const mirror = mirrorInnerRef.current
    const el = fieldRef.current
    if (wrap == null || mirror == null || el == null) {
      setFakeCaret(null)
      return
    }
    if (document.activeElement !== el) {
      setFakeCaret(null)
      return
    }
    const lineHeightRaw = parseFloat(getComputedStyle(el).lineHeight)
    const lineHeight = Number.isFinite(lineHeightRaw) && lineHeightRaw > 0 ? lineHeightRaw : 18
    const start = el.selectionStart ?? el.value.length
    const end = el.selectionEnd ?? el.value.length
    const caretIdx = start !== end ? end : start
    const pos = richMirrorCaretPositionInRoot(mirror, wrap, value, caretIdx, lineHeight)
    const caretColor = getComputedStyle(el).caretColor || 'CanvasText'
    if (pos == null) {
      setFakeCaret(null)
      return
    }
    setFakeCaret({ ...pos, caretColor })
  }, [value, measureTick, scrollMirror.x, scrollMirror.y, fieldRef])

  useEffect(() => {
    const onSel = () => {
      const el = fieldRef.current
      if (el != null && document.activeElement === el) {
        setMeasureTick((n) => n + 1)
      }
    }
    document.addEventListener('selectionchange', onSel)
    return () => document.removeEventListener('selectionchange', onSel)
  }, [fieldRef])

  useLayoutEffect(() => {
    const wrap = wrapperRef.current
    if (wrap == null || typeof ResizeObserver === 'undefined') {
      return
    }
    const ro = new ResizeObserver(() => {
      setMeasureTick((n) => n + 1)
    })
    ro.observe(wrap)
    return () => ro.disconnect()
  }, [])

  return { wrapperRef, mirrorInnerRef, fakeCaret, bumpMeasure }
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
  inlineMovieCardRefs?: ReadonlyMap<number, InlineMovieCardRefMeta>
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
      inlineMovieCardRefs,
    },
    ref,
  ) {
    const [scrollLeft, setScrollLeft] = useState(0)
    const fieldRef = useRef<HTMLInputElement | null>(null)
    const { wrapperRef, mirrorInnerRef, fakeCaret, bumpMeasure } = useFakeCaretOverlay(value, fieldRef, {
      x: scrollLeft,
      y: 0,
    })

    const setRefs = useCallback(
      (node: HTMLInputElement | null) => {
        fieldRef.current = node
        assignRef(node, ref)
      },
      [ref],
    )

    return (
      <div
        ref={wrapperRef}
        className={`group relative min-h-8 min-w-0 flex-1 rounded-lg border border-(--tgui--divider_color) bg-(--tgui--bg_color) focus-within:border-transparent focus-within:ring-2 focus-within:ring-(--tgui--link_color) ${wrapperClassName}`}
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 z-0 overflow-hidden rounded-[inherit] px-2.5 py-1.5"
        >
          <div
            ref={mirrorInnerRef}
            className="inline-block min-h-5 whitespace-nowrap text-[13px] leading-normal text-(--tgui--text_color)"
            style={{ transform: `translateX(-${scrollLeft}px)` }}
          >
            {value.length === 0 ? (
              <span className="text-[13px] leading-normal text-(--tgui--hint_color)">{placeholder}</span>
            ) : (
              <CommentBodyWithReactionTokens
                text={value}
                annotateCharRanges
                inlineMovieCardRefs={inlineMovieCardRefs}
                className="text-[13px] leading-normal text-(--tgui--text_color)"
              />
            )}
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
          onChange={(e) => {
            onChange(e.currentTarget.value)
            bumpMeasure()
          }}
          onScroll={(e) => {
            setScrollLeft(e.currentTarget.scrollLeft)
            bumpMeasure()
          }}
          onKeyDown={(e) => {
            onKeyDown?.(e)
            bumpMeasure()
          }}
          onKeyUp={bumpMeasure}
          onSelect={bumpMeasure}
          onFocus={bumpMeasure}
          onBlur={bumpMeasure}
          className={`relative z-10 min-h-8 w-full bg-transparent px-2.5 py-1.5 text-[13px] leading-normal text-transparent caret-transparent outline-none selection:bg-[color-mix(in_srgb,var(--tgui--link_color)_24%,transparent)] disabled:opacity-50 ${inputClassName}`}
        />
        {fakeCaret != null ? (
          <span
            aria-hidden
            className="pointer-events-none absolute z-30 w-px rounded-[1px]"
            style={{
              left: fakeCaret.left,
              top: fakeCaret.top,
              height: Math.max(fakeCaret.height, 12),
              backgroundColor: fakeCaret.caretColor,
            }}
          />
        ) : null}
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
  /** Цвет текста в зеркале (реакции, @-чипы, обычный текст). */
  mirrorOverlayTextClassName?: string
  /** Цвет плейсхолдера в зеркале, когда поле пустое. */
  mirrorPlaceholderClassName?: string
  rows?: number
  inlineMovieCardRefs?: ReadonlyMap<number, InlineMovieCardRefMeta>
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
      inlineMovieCardRefs,
    },
    ref,
  ) {
    const [scrollTop, setScrollTop] = useState(0)
    const fieldRef = useRef<HTMLTextAreaElement | null>(null)
    const { wrapperRef, mirrorInnerRef, fakeCaret, bumpMeasure } = useFakeCaretOverlay(value, fieldRef, {
      x: 0,
      y: scrollTop,
    })

    const setRefs = useCallback(
      (node: HTMLTextAreaElement | null) => {
        fieldRef.current = node
        assignRef(node, ref)
      },
      [ref],
    )

    const handleKeyUp = useCallback(
      (e: KeyboardEvent<HTMLTextAreaElement>) => {
        onKeyUp?.(e)
        bumpMeasure()
      },
      [onKeyUp, bumpMeasure],
    )

    const handleSelect = useCallback(
      (e: SyntheticEvent<HTMLTextAreaElement>) => {
        onSelect?.(e)
        bumpMeasure()
      },
      [onSelect, bumpMeasure],
    )

    return (
      <div
        ref={wrapperRef}
        className={`relative min-h-24 min-w-0 flex-1 rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) ${wrapperClassName}`}
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 z-0 overflow-hidden rounded-[inherit] px-3 py-2"
        >
          <div
            ref={mirrorInnerRef}
            className={`wrap-break-word whitespace-pre-wrap text-sm leading-normal ${mirrorOverlayTextClassName}`}
            style={{ transform: `translateY(-${scrollTop}px)` }}
          >
            {value.length === 0 ? (
              <span className={`text-sm leading-normal ${mirrorPlaceholderClassName}`}>{placeholder}</span>
            ) : (
              <CommentBodyWithReactionTokens
                text={value}
                annotateCharRanges
                inlineMovieCardRefs={inlineMovieCardRefs}
                className={`wrap-break-word whitespace-pre-wrap text-sm leading-normal ${mirrorOverlayTextClassName}`}
              />
            )}
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
            bumpMeasure()
          }}
          onScroll={(e) => {
            setScrollTop(e.currentTarget.scrollTop)
            bumpMeasure()
          }}
          onKeyDown={(e) => {
            onKeyDown?.(e)
            bumpMeasure()
          }}
          onKeyUp={handleKeyUp}
          onSelect={handleSelect}
          onFocus={bumpMeasure}
          onBlur={bumpMeasure}
          className={`relative z-10 min-h-24 w-full resize-y wrap-break-word bg-transparent px-3 py-2 text-sm leading-normal whitespace-pre-wrap text-transparent caret-transparent outline-none selection:bg-[color-mix(in_srgb,var(--tgui--link_color)_24%,transparent)] disabled:opacity-50 ${textareaClassName}`}
        />
        {fakeCaret != null ? (
          <span
            aria-hidden
            className="pointer-events-none absolute z-30 w-px rounded-[1px]"
            style={{
              left: fakeCaret.left,
              top: fakeCaret.top,
              height: Math.max(fakeCaret.height, 12),
              backgroundColor: fakeCaret.caretColor,
            }}
          />
        ) : null}
      </div>
    )
  },
)
