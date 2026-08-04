import { IconButton } from '@telegram-apps/telegram-ui'
import { MoreHorizontal, Pencil, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useRef, useState, type MouseEvent } from 'react'

const POST_OWNER_ACTION_LABELS = {
  edit: 'Изменить',
  delete: 'Удалить',
  deleteBusy: 'Удаление…',
} as const

export type PostHeaderActionsProps = {
  canManage?: boolean
  onEdit?: () => void
  onDelete?: () => void
  busy?: boolean
  deleteBusy?: boolean
  disabled?: boolean
}

const ICON_BUTTON_CLASS =
  'relative z-0 box-border! flex! h-8! w-8! min-h-8! min-w-8! shrink-0 items-center! justify-center! rounded-full p-0! leading-none! text-(--tgui--hint_color) transition-[transform,colors] hover:text-(--tgui--text_color) active:scale-[0.97] aria-expanded:text-(--tgui--link_color)!'

const ICON_CLASS = 'relative z-1 block shrink-0 size-4'

const MENU_POP_CLASS =
  'filmony-detail-menu-pop absolute right-0 top-10 z-30 w-48 rounded-2xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-2 shadow-xl ring-1 ring-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_12%,transparent)]'

const MENU_ITEM_CLASS =
  'flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-base hover:bg-(--tgui--secondary_bg_color) disabled:opacity-50'

export function PostHeaderActions({
  canManage = false,
  onEdit,
  onDelete,
  busy = false,
  deleteBusy = false,
  disabled = false,
}: PostHeaderActionsProps) {
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const hasOwnerActions = onEdit != null || onDelete != null
  const showMenuTrigger = canManage || hasOwnerActions
  const controlsDisabled = disabled || busy

  const closeMenu = useCallback(() => {
    setMenuOpen(false)
  }, [])

  useEffect(() => {
    if (!menuOpen) return undefined

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') closeMenu()
    }

    const onPointerDown = (event: globalThis.MouseEvent) => {
      const root = menuRef.current
      if (root != null && !root.contains(event.target as Node)) {
        closeMenu()
      }
    }

    window.addEventListener('keydown', onKeyDown)
    document.addEventListener('mousedown', onPointerDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      document.removeEventListener('mousedown', onPointerDown)
    }
  }, [menuOpen, closeMenu])

  const runMenuAction = (action: () => void) => {
    closeMenu()
    action()
  }

  if (!showMenuTrigger) {
    return null
  }

  return (
    <div className="relative shrink-0" ref={menuRef}>
      <IconButton
        type="button"
        size="s"
        mode="gray"
        disabled={controlsDisabled}
        onClick={(event: MouseEvent<HTMLButtonElement>) => {
          event.stopPropagation()
          setMenuOpen((wasOpen) => !wasOpen)
        }}
        aria-expanded={menuOpen}
        aria-label="Ещё"
        aria-haspopup="menu"
        className={ICON_BUTTON_CLASS}
      >
        <MoreHorizontal
          className={ICON_CLASS}
          strokeWidth={1.75}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        />
      </IconButton>

      {menuOpen ? (
        <div className={MENU_POP_CLASS} role="menu">
          {onEdit != null ? (
            <button
              type="button"
              role="menuitem"
              disabled={controlsDisabled || deleteBusy}
              onClick={() => runMenuAction(onEdit)}
              className={MENU_ITEM_CLASS}
            >
              <Pencil className="size-4 shrink-0" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" aria-hidden />
              {POST_OWNER_ACTION_LABELS.edit}
            </button>
          ) : null}

          {onDelete != null ? (
            <button
              type="button"
              role="menuitem"
              disabled={controlsDisabled || deleteBusy}
              onClick={() => runMenuAction(onDelete)}
              className={`${onEdit != null ? 'mt-1 ' : ''}${MENU_ITEM_CLASS} text-(--tgui--destructive_text_color)`}
            >
              <Trash2 className="size-4 shrink-0" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" aria-hidden />
              {deleteBusy ? POST_OWNER_ACTION_LABELS.deleteBusy : POST_OWNER_ACTION_LABELS.delete}
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
