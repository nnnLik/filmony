export type FilmGenreChipsProps = {
  genres: string[]
  /** Сколько жанров показать; остальные сворачиваются в «+N». Без лимита — все. */
  maxVisible?: number
  /** `sm` — лента и компактные блоки; `md` — страница карточки / каталог */
  size?: 'sm' | 'md'
  className?: string
}

const CHIP_SM =
  'shrink-0 rounded-md border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_38%,transparent)] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_12%,transparent)] px-1.5 py-0.5 text-[10px] font-medium leading-tight text-(--tgui--text_color)'
const CHIP_MD =
  'shrink-0 rounded-lg border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_38%,transparent)] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_12%,transparent)] px-2 py-0.5 text-[11px] font-medium leading-tight text-(--tgui--text_color)'

/**
 * Жанры из записи каталога (часто Кинопоиск): чипы в общей стилистике ленты (mint).
 */
export function FilmGenreChips({
  genres,
  maxVisible,
  size = 'sm',
  className = '',
}: FilmGenreChipsProps) {
  const trimmed = genres.map((g) => g.trim()).filter((g) => g.length > 0)
  if (trimmed.length === 0) return null

  const cap = maxVisible != null ? maxVisible : trimmed.length
  const shown = trimmed.slice(0, cap)
  const remainder = trimmed.length - shown.length
  const chipClass = size === 'md' ? CHIP_MD : CHIP_SM
  const moreClass =
    size === 'md'
      ? 'text-[11px] font-semibold text-(--tgui--hint_color)'
      : 'text-[10px] font-semibold text-(--tgui--hint_color)'

  return (
    <div
      className={`flex max-w-full flex-wrap items-center gap-0.5 ${className}`.trim()}
      role="list"
      aria-label="Жанры из каталога"
    >
      {shown.map((g, i) => (
        <span key={`${g}-${i}`} role="listitem" className={chipClass} title={g}>
          {g}
        </span>
      ))}
      {remainder > 0 ? <span className={moreClass}>+{remainder}</span> : null}
    </div>
  )
}
