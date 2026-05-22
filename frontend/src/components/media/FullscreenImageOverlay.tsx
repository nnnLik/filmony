import { IconButton } from '@telegram-apps/telegram-ui'
import { X } from 'lucide-react'
import { useCallback, useEffect } from 'react'
import { createPortal } from 'react-dom'

export type FullscreenImageOverlayProps = {
  /** When false, renders nothing */
  open: boolean
  src: string
  alt?: string
  onClose: () => void
}

/**
 * Full-viewport overlay for viewing one image without cropping (`object-contain`).
 * Closes via backdrop click, Escape, or the close button.
 */
export function FullscreenImageOverlay({ open, src, alt = '', onClose }: FullscreenImageOverlayProps) {
  const onKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!open) return
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    },
    [open, onClose],
  )

  useEffect(() => {
    if (!open) return
    window.addEventListener('keydown', onKeyDown)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = prevOverflow
    }
  }, [open, onKeyDown])

  if (!open) return null

  return createPortal(
    <div className="filmony-theme fixed inset-0 z-200 flex flex-col bg-black/86 backdrop-blur-sm" role="dialog" aria-modal="true" aria-label="Просмотр изображения">
      <div className="flex shrink-0 items-center justify-end gap-2 px-2 py-2 sm:px-3">
        <IconButton type="button" mode="gray" size="s" aria-label="Закрыть" title="Закрыть" onClick={onClose}>
          <X className="relative z-1 block size-5" strokeWidth={2} aria-hidden />
        </IconButton>
      </div>
      <button
        type="button"
        aria-label="Закрыть просмотр (нажатие по фону)"
        className="relative mx-auto mb-6 min-h-0 w-full flex-1 touch-pan-y px-4 outline-none!"
        onClick={onClose}
      >
        <span className="pointer-events-none flex h-full max-h-[min(100vh,720px)] w-full items-center justify-center px-2 sm:max-h-[85dvh]">
          <img
            src={src}
            alt={alt}
            className="max-h-full max-w-full object-contain select-none"
            draggable={false}
            onClick={(e) => e.stopPropagation()}
          />
        </span>
      </button>
    </div>,
    document.body,
  )
}
