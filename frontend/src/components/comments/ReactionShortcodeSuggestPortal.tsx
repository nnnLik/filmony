import { createPortal } from 'react-dom'

import type { ReactionCatalogItem } from '../../api/profileTypes'
import { resolveApiMediaUrl } from '../../lib/resolveApiMediaUrl'

type PopoverLayout = {
  top: number
  left: number
  width: number
  maxHeight: number
}

export type ReactionShortcodeSuggestPortalProps = {
  layout: PopoverLayout
  items: readonly ReactionCatalogItem[]
  highlightIdx: number
  catalogPending: boolean
  onPick: (item: ReactionCatalogItem) => void
  onDismiss: () => void
}

export function ReactionShortcodeSuggestPortal({
  layout,
  items,
  highlightIdx,
  catalogPending,
  onPick,
  onDismiss,
}: ReactionShortcodeSuggestPortalProps) {
  return createPortal(
    <>
      <button
        type="button"
        tabIndex={-1}
        aria-hidden
        className="fixed inset-0 z-200 cursor-default bg-black/0"
        onClick={onDismiss}
      />
      <div
        className="filmony-theme fixed z-201 overflow-y-auto rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) py-1 shadow-lg"
        style={{
          top: layout.top,
          left: layout.left,
          width: layout.width,
          maxHeight: layout.maxHeight,
        }}
        role="listbox"
        aria-label="Вставить реакцию"
      >
        {catalogPending && items.length === 0 ? (
          <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Загрузка…</p>
        ) : items.length === 0 ? (
          <p className="px-3 py-2 text-[12px] text-(--tgui--hint_color)">Нет совпадений</p>
        ) : (
          items.map((item, idx) => {
            const selected = idx === highlightIdx
            return (
              <button
                key={item.id}
                type="button"
                role="option"
                aria-selected={selected}
                className={`flex w-full items-center gap-2 px-3 py-1.5 text-left transition active:opacity-90 ${
                  selected
                    ? 'bg-[color-mix(in_srgb,var(--filmony-amber,#e8b86d)_12%,var(--tgui--secondary_bg_color))]'
                    : 'hover:bg-(--tgui--secondary_bg_color)'
                }`}
                onMouseDown={(ev) => {
                  ev.preventDefault()
                  onPick(item)
                }}
              >
                <img
                  src={resolveApiMediaUrl(item.image_url)}
                  alt=""
                  width={20}
                  height={20}
                  className="size-5 shrink-0 object-contain"
                />
                <span className="font-mono text-[13px] text-(--tgui--text_color)">:{item.shortcode}:</span>
              </button>
            )
          })
        )}
      </div>
    </>,
    document.body,
  )
}
