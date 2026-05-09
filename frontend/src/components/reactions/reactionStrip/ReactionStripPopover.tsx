import type { CSSProperties } from 'react'

import type {
  ReactionCatalogItem,
  ReactionCatalogTab,
  ReactionGroupedCatalog,
  ReactionCountItem,
} from '../../../api/profileTypes'
import { PICK_BG, PICK_BORDER, PICK_SURFACE } from './constants'
import { ReactionThumb } from './ReactionThumb'

export type ReactionStripPopoverProps = {
  closePicker: () => void
  popoverStyle: CSSProperties
  placeAbove: boolean
  catalogError: string | null
  catalog: ReactionGroupedCatalog | null
  busy: boolean
  effectiveTabSlug: string | null
  onTabSelect: (categorySlug: string) => void
  compact: boolean
  /** Меньшие миниатюры и типографика в том же по ширине окне. */
  contentDensity?: 'default' | 'dense'
  myReactionIds: Set<number>
  countsById: Map<number, ReactionCountItem>
  apply: (reactionTypeId: number) => void
  recentItems: ReactionCatalogItem[]
  gridItems: ReactionCatalogItem[]
  activeTab: ReactionCatalogTab | null
}

export function ReactionStripPopover({
  closePicker,
  popoverStyle,
  placeAbove,
  catalogError,
  catalog,
  busy,
  effectiveTabSlug,
  onTabSelect,
  compact,
  contentDensity = 'default',
  myReactionIds,
  countsById,
  apply,
  recentItems,
  gridItems,
  activeTab,
}: ReactionStripPopoverProps) {
  const dense = compact && contentDensity === 'dense'

  return (
    <>
      <button
        type="button"
        aria-label="Закрыть"
        tabIndex={-1}
        className="fixed inset-0 z-199 cursor-default bg-black/72"
        onClick={closePicker}
      />
      <div
        role="dialog"
        aria-label="Выбор реакции"
        className={`fixed z-200 flex flex-col overflow-hidden rounded-[20px] border ${PICK_BORDER} ${PICK_BG} shadow-[0_16px_48px_rgba(0,0,0,0.55)]`}
        style={popoverStyle}
      >
        <div
          className={`pointer-events-none absolute left-1/2 size-3 -translate-x-1/2 rotate-45 ${PICK_BORDER} ${PICK_BG} border shadow-sm ${
            placeAbove ? 'bottom-[-5px] border-r border-b border-t-0 border-l-0' : '-top-[5px] border-l border-t border-r-0 border-b-0'
          }`}
          aria-hidden
        />

        <div className={`relative z-1 flex min-h-0 flex-1 flex-col ${dense ? 'px-3 pt-3 pb-2' : 'px-2.5 pt-2.5 pb-2'}`}>
          <div className="flex min-h-0 flex-1 gap-0 overflow-hidden">
            {catalogError != null ? (
              <p className="w-full px-2 py-6 text-center text-[12px] text-red-400">{catalogError}</p>
            ) : null}
            {catalog === null && catalogError == null ? (
              <p className={`w-full px-2 text-center text-zinc-500 ${dense ? 'py-6 text-[12px]' : 'py-8 text-[13px]'}`}>Загрузка…</p>
            ) : null}
            {catalog != null && catalog.tabs.length > 0 ? (
              <>
                <nav
                  className={`flex shrink-0 flex-col overflow-y-auto overscroll-contain border-r pb-1 pl-1 [-webkit-overflow-scrolling:touch] ${PICK_BORDER} ${
                    dense ? 'w-[62px] gap-0.5 pr-1.5' : 'w-[76px] gap-1 pr-2'
                  }`}
                >
                  <span
                    className={`pb-0.5 font-semibold uppercase tracking-wide text-zinc-500 ${dense ? 'px-1 text-[7px]' : 'px-1.5 text-[9px]'}`}
                  >
                    Коллекции
                  </span>
                  {catalog.tabs.map((tab) => {
                    const sel = tab.category_slug === effectiveTabSlug
                    return (
                      <button
                        key={tab.category_slug}
                        type="button"
                        disabled={busy}
                        onClick={() => onTabSelect(tab.category_slug)}
                        className={`rounded-lg text-left font-medium transition-colors disabled:opacity-50 ${
                          dense ? 'px-1.5 py-1 text-[11px]' : 'px-2 py-2 text-[12px]'
                        } ${
                          sel ? `${PICK_SURFACE} font-semibold text-white` : 'text-zinc-400 hover:bg-[#252528] hover:text-zinc-200'
                        }`}
                      >
                        {tab.label}
                      </button>
                    )
                  })}
                </nav>

                <div className={`flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto overscroll-contain pr-0.5 [-webkit-overflow-scrolling:touch] ${dense ? 'gap-1.5 pl-2' : 'gap-2 pl-3'}`}>
                  {recentItems.length > 0 ? (
                    <div className="shrink-0">
                      <p
                        className={`shrink-0 font-medium tracking-tight text-zinc-200 ${dense ? 'mb-1 text-[10px]' : 'mb-1.5 text-[11px]'}`}
                      >
                        Недавние
                      </p>
                      <div className="-mx-0.5 flex gap-1 overflow-x-auto pb-1 [-webkit-overflow-scrolling:touch]">
                        {recentItems.map((item) => {
                          const mine = myReactionIds.has(item.id)
                          const badge = countsById.get(item.id)
                          return (
                            <button
                              key={`r-${item.id}`}
                              type="button"
                              disabled={busy}
                              onClick={() => void apply(item.id)}
                              className={`relative shrink-0 rounded-lg transition-[transform,opacity] active:scale-95 disabled:opacity-50 ${
                                dense ? 'p-[1px]' : 'p-[2px]'
                              } ${
                                mine
                                  ? dense
                                    ? 'ring-[1.5px] ring-[#4ade80]'
                                    : 'ring-2 ring-[#4ade80]'
                                  : dense
                                    ? 'ring-0 hover:ring-1 hover:ring-zinc-600'
                                    : 'ring-1 ring-transparent hover:ring-zinc-600'
                              }`}
                            >
                              <ReactionThumb
                                src={item.image_url}
                                className={dense ? 'size-9' : compact ? 'size-12' : 'size-9'}
                                roundedClassName="rounded-md"
                              />
                              {badge != null ? (
                                <span
                                  className={`absolute -bottom-0.5 -right-0.5 flex items-center justify-center rounded-full bg-emerald-500 px-0.5 font-bold leading-none text-white shadow-sm tabular-nums ${
                                    dense ? 'min-h-[11px] min-w-[11px] text-[7px]' : 'min-h-[14px] min-w-[14px] text-[8px]'
                                  }`}
                                >
                                  {badge.count}
                                </span>
                              ) : null}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  ) : catalog.recent.length === 0 ? (
                    <p className={`shrink-0 text-zinc-500 ${dense ? 'text-[10px]' : 'text-[11px]'}`}>Выберите коллекцию слева.</p>
                  ) : null}

                  {activeTab != null ? (
                    <div className="flex min-h-[72px] min-w-0 flex-1 flex-col">
                      <p
                        className={`shrink-0 font-medium tracking-tight text-zinc-200 ${
                          dense ? 'mb-1 text-[10px]' : 'mb-1.5 text-[11px]'
                        }`}
                      >
                        {activeTab.label}
                      </p>
                      <div
                        className={`grid shrink-0 gap-1 pb-2 ${dense ? 'grid-cols-4' : compact ? 'grid-cols-3 sm:grid-cols-4' : 'grid-cols-5'}`}
                      >
                        {gridItems.map((item) => {
                          const mine = myReactionIds.has(item.id)
                          return (
                            <button
                              key={item.id}
                              type="button"
                              disabled={busy}
                              onClick={() => void apply(item.id)}
                              title={
                                item.asset_key.includes('/')
                                  ? item.asset_key.split('/').filter(Boolean).pop() ?? item.asset_key
                                  : item.asset_key
                              }
                              className={`aspect-square shrink-0 touch-manipulation rounded-lg transition-transform active:scale-90 disabled:opacity-40 ${
                                dense ? 'p-px' : 'p-[2px]'
                              } ${
                                mine
                                  ? dense
                                    ? 'ring-[1.5px] ring-[#4ade80] ring-offset-0 ring-offset-[#121212]'
                                    : 'ring-2 ring-[#4ade80] ring-offset-1 ring-offset-[#121212]'
                                  : 'ring-0 hover:ring-1 hover:ring-zinc-600'
                              }`}
                            >
                              <ReactionThumb src={item.image_url} className="size-full" roundedClassName="rounded-md" />
                            </button>
                          )
                        })}
                        {gridItems.length === 0 ? (
                          <p className={`col-span-full py-8 text-center text-zinc-500 ${dense ? 'text-[11px]' : 'text-[12px]'}`}>
                            Ничего не нашлось
                          </p>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                </div>
              </>
            ) : null}
          </div>
        </div>
      </div>
    </>
  )
}
