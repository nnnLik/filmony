import { useMemo, type ImgHTMLAttributes } from 'react'

import { useFullscreenImageActivator } from '../../hooks/useFullscreenImageActivator'

export type FeedContainedImageBackdropProps = {
  /** Absolute or resolved image URL */
  src: string
  /** Accessible label for the sharp foreground image */
  alt: string
  /** Outer framing box (default `relative w-full`; use `absolute inset-0 size-full` inside ratio-locked previews) */
  frameClassName?: string
  /** Foreground `<img>` — must retain `object-contain` where non-distorting fit is required */
  foregroundClassName: string
  loading?: ImgHTMLAttributes<HTMLImageElement>['loading']
}

/**
 * Crisp `object-contain` foreground plus a softened, cropped duplicate layer so letterboxing
 * areas read as filled edges instead of empty bars (feed list previews).
 */
export function FeedContainedImageBackdrop({
  src,
  alt,
  frameClassName = 'relative w-full',
  foregroundClassName,
  loading = 'lazy',
}: FeedContainedImageBackdropProps) {
  const trimmed = src.trim()
  if (trimmed === '') return null

  const frameCls = `isolate overflow-hidden ${frameClassName}`.trim()

  return (
    <div className={frameCls}>
      <img
        src={trimmed}
        alt=""
        aria-hidden
        className="pointer-events-none absolute inset-0 z-0 size-full origin-center scale-110 transform-gpu object-cover opacity-50 blur-2xl"
        loading={loading}
        draggable={false}
      />
      <img
        src={trimmed}
        alt={alt}
        className={[foregroundClassName, 'z-[1]'].filter(Boolean).join(' ')}
        loading={loading}
        draggable={false}
      />
    </div>
  )
}

type FeedOpenableContainedImageProps = {
  /** Absolute or resolved image URL */
  src: string
  alt?: string
  wrapperClassName?: string
  imgClassName?: string
  /**
   * When true, renders a blurred `object-cover` underlayer beneath the foreground `img`
   * (still `object-contain` via `imgClassName`) so mismatched aspects do not show hard bars.
   */
  backdropFill?: boolean
  loading?: ImgHTMLAttributes<HTMLImageElement>['loading']
  /** When provided, plain activation navigates/runs after defer; omit for double-open-only surfaces */
  onSingleNavigate?: (() => void) | null
  /** For link-like surfaces: exposes Enter/Space when `onSingleNavigate` is set */
  ariaLabel?: string
}

function FeedOpenableContainedImageInner({
  src,
  alt = '',
  wrapperClassName = '',
  imgClassName,
  backdropFill = false,
  loading = 'lazy',
  onSingleNavigate = null,
  ariaLabel,
}: FeedOpenableContainedImageProps) {
  const trimmed = src.trim()
  const enabled = trimmed !== ''

  const activator = useFullscreenImageActivator({
    enabled,
    imageSrc: trimmed,
    imageAlt: ariaLabel ?? alt ?? 'Изображение',
    onSingleNavigate: onSingleNavigate ?? undefined,
  })

  const role = useMemo<'link' | 'presentation' | 'button'>(() => {
    if (typeof onSingleNavigate === 'function') return 'link'
    return 'presentation'
  }, [onSingleNavigate])

  if (!enabled) return null

  const isDecorativeInteractive = typeof onSingleNavigate !== 'function'

  const body =
    backdropFill ? (
      <FeedContainedImageBackdrop
        src={trimmed}
        alt={alt || ''}
        foregroundClassName={imgClassName ?? 'w-full max-w-full object-contain object-center'}
        loading={loading}
      />
    ) : (
      <img src={trimmed} alt={alt || ''} className={imgClassName} loading={loading} draggable={false} />
    )

  return (
    <>
      <div
        {...activator.bindings}
        tabIndex={typeof onSingleNavigate === 'function' ? 0 : -1}
        role={role}
        aria-hidden={isDecorativeInteractive ? true : undefined}
        aria-label={
          typeof onSingleNavigate === 'function'
            ? ariaLabel ?? 'Открыть'
            : undefined
        }
        className={wrapperClassName}
      >
        {body}
      </div>
      {activator.overlay}
    </>
  )
}

export function FeedOpenableContainedImage(props: FeedOpenableContainedImageProps) {
  return <FeedOpenableContainedImageInner {...props} />
}

/** Thumbnail inside a Link: fullscreen on double activation; single tap keeps default link behavior */
export function FeedOpenableContainedImageThumbnail({
  src,
  alt = '',
  wrapperClassName = '',
  imgClassName,
  backdropFill = false,
  loading = 'lazy',
}: Omit<FeedOpenableContainedImageProps, 'onSingleNavigate' | 'ariaLabel'>) {
  return (
    <FeedOpenableContainedImageInner
      src={src}
      alt={alt}
      wrapperClassName={wrapperClassName}
      imgClassName={imgClassName}
      backdropFill={backdropFill}
      loading={loading}
      onSingleNavigate={null}
    />
  )
}
