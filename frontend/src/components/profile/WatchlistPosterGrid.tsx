import { IconButton } from '@telegram-apps/telegram-ui'
import { MoreVertical, Users } from 'lucide-react'
import { useCallback, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import type { WatchlistEntryItem } from '../../api/profileTypes'

type WatchlistPosterGridProps = {
  items: WatchlistEntryItem[]
  /** When true, entries can be removed via long-press or menu. */
  canManage?: boolean
  onDeleteEntry?: (entryId: number) => void | Promise<void>
}

function watchlistItemHref(item: WatchlistEntryItem): string | null {
  if (item.provider === 'kinopoisk' && item.film_id != null && item.film_id > 0) {
    return `/films/${encodeURIComponent(String(item.film_id))}`
  }
  if (item.provider === 'rawg' && item.catalog_item_id != null && item.catalog_item_id > 0) {
    return '/cards/new'
  }
  if (item.provider === 'custom' || item.provider === 'no_provider') {
    return '/cards/new'
  }
  return null
}

function watchlistItemTitle(item: WatchlistEntryItem): string {
  return item.title || item.film_title || 'Untitled'
}

function watchlistItemPoster(item: WatchlistEntryItem): string | null {
  return item.poster_url ?? item.film_poster_url ?? null
}

const LONG_PRESS_MS = 450

function WatchlistPosterCell({
  item,
  canManage,
  onDeleteEntry,
}: {
  item: WatchlistEntryItem
  canManage: boolean
  onDeleteEntry?: (entryId: number) => void | Promise<void>
}) {
  const title = watchlistItemTitle(item)
  const poster = watchlistItemPoster(item)
  const href = watchlistItemHref(item)
  const hasWatchWith =
    (item.watch_with_user_ids != null && item.watch_with_user_ids.length > 0) ||
    (item.watch_with_user_id != null && item.watch_with_user_id !== '')
  const [menuOpen, setMenuOpen] = useState(false)
  const longPressTimer = useRef<number | null>(null)

  const clearLongPress = useCallback(() => {
    if (longPressTimer.current != null) {
      window.clearTimeout(longPressTimer.current)
      longPressTimer.current = null
    }
  }, [])

  const requestDelete = useCallback(() => {
    setMenuOpen(false)
    if (onDeleteEntry == null) return
    const ok = window.confirm(`Убрать «${title}» из списка «Позже»?`)
    if (!ok) return
    void onDeleteEntry(item.entry_id)
  }, [item.entry_id, onDeleteEntry, title])

  const onPointerDown = useCallback(() => {
    if (!canManage || onDeleteEntry == null) return
    clearLongPress()
    longPressTimer.current = window.setTimeout(() => {
      longPressTimer.current = null
      requestDelete()
    }, LONG_PRESS_MS)
  }, [canManage, clearLongPress, onDeleteEntry, requestDelete])

  const badge = hasWatchWith ? (
    <span
      className="absolute bottom-1.5 left-1.5 flex items-center gap-0.5 rounded-md bg-[color-mix(in_srgb,var(--tgui--bg_color)_82%,transparent)] px-1.5 py-0.5 text-[10px] font-medium text-(--tgui--text_color) shadow-sm backdrop-blur-sm"
      title="Смотреть вместе"
    >
      <Users className="block" size={11} strokeWidth={2} aria-hidden />
      Вместе
    </span>
  ) : null

  const manageMenu =
    canManage && onDeleteEntry != null ? (
      <div className="absolute right-1 top-1 z-10">
        <IconButton
          type="button"
          size="s"
          mode="plain"
          aria-label="Действия со списком «Позже»"
          className="rounded-lg! bg-[color-mix(in_srgb,var(--tgui--bg_color)_75%,transparent)] backdrop-blur-sm"
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            setMenuOpen((v) => !v)
          }}
        >
          <MoreVertical className="block" size={16} strokeWidth={2} />
        </IconButton>
        {menuOpen ? (
          <div className="absolute right-0 mt-1 min-w-[9rem] overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) shadow-lg">
            <button
              type="button"
              className="w-full px-3 py-2 text-left text-xs text-(--tgui--destructive_text_color) active:bg-(--tgui--secondary_bg_color)"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                requestDelete()
              }}
            >
              Убрать из «Позже»
            </button>
          </div>
        ) : null}
      </div>
    ) : null

  const inner = (
    <div
      className="relative aspect-2/3 w-full"
      onPointerDown={onPointerDown}
      onPointerUp={clearLongPress}
      onPointerLeave={clearLongPress}
      onPointerCancel={clearLongPress}
    >
      {poster ? (
        <img src={poster} alt={title} className="h-full w-full object-cover" />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-[11px] text-(--tgui--hint_color)">
          Нет постера
        </div>
      )}
      {badge}
      {manageMenu}
    </div>
  )

  const shellClass =
    'relative block overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)'

  if (href == null) {
    return (
      <div className={shellClass} aria-label={`«${title}» в списке «Позже»`}>
        {inner}
      </div>
    )
  }

  return (
    <Link
      to={href}
      className={`${shellClass} no-underline`}
      aria-label={`Открыть «${title}»`}
      onClick={() => setMenuOpen(false)}
    >
      {inner}
    </Link>
  )
}

export function WatchlistPosterGrid({ items, canManage = false, onDeleteEntry }: WatchlistPosterGridProps) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {items.map((item) => (
        <WatchlistPosterCell
          key={item.entry_id}
          item={item}
          canManage={canManage}
          onDeleteEntry={onDeleteEntry}
        />
      ))}
    </div>
  )
}
