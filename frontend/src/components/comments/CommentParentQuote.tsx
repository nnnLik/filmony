import { Link } from 'react-router'
import type { MouseEventHandler } from 'react'

export type CommentParentQuoteVariant = 'button' | 'link'

export type CommentParentQuoteProps = {
  variant: CommentParentQuoteVariant
  authorLabel: string
  textPreview: string
  missingHint?: string
  disabled?: boolean
  onActivate?: () => void
  href?: string
  linkState?: unknown
  onMouseDown?: MouseEventHandler
}

const QUOTE_CLASS =
  'mt-2 block w-full rounded-lg border-l-2 border-(--tgui--link_color) bg-(--tgui--secondary_bg_color) px-2 py-1 text-left'

export function CommentParentQuote({
  variant,
  authorLabel,
  textPreview,
  missingHint: _missingHint = 'Нажмите, чтобы подгрузить и перейти',
  disabled = false,
  onActivate,
  href,
  linkState,
  onMouseDown,
}: CommentParentQuoteProps) {
  const content = (
    <>
      <p className="truncate text-xs font-medium text-(--tgui--link_color)">{authorLabel}</p>
      <p className="truncate text-xs text-(--tgui--hint_color)">{textPreview}</p>
    </>
  )

  if (variant === 'link' && href != null) {
    return (
      <Link
        to={href}
        state={linkState}
        className={`${QUOTE_CLASS} no-underline active:opacity-90`}
        onMouseDown={onMouseDown}
      >
        {content}
      </Link>
    )
  }

  return (
    <button
      type="button"
      onClick={onActivate}
      className={QUOTE_CLASS}
      disabled={disabled}
      onMouseDown={onMouseDown}
    >
      {content}
    </button>
  )
}
