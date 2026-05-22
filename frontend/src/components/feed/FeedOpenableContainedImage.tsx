import { useMemo, type ImgHTMLAttributes } from 'react'

import { useFullscreenImageActivator } from '../../hooks/useFullscreenImageActivator'

type FeedOpenableContainedImageProps = {
  /** Absolute or resolved image URL */
  src: string
  alt?: string
  wrapperClassName?: string
  imgClassName?: string
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
        <img src={trimmed} alt={alt || ''} className={imgClassName} loading={loading} draggable={false} />
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
  loading = 'lazy',
}: Omit<FeedOpenableContainedImageProps, 'onSingleNavigate' | 'ariaLabel'>) {
  return (
    <FeedOpenableContainedImageInner
      src={src}
      alt={alt}
      wrapperClassName={wrapperClassName}
      imgClassName={imgClassName}
      loading={loading}
      onSingleNavigate={null}
    />
  )
}
