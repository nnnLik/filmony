import type { UserCardCategorySnippet } from '../../api/profileTypes'

/** Small shelf label derived from GET card payload (`category`). */
export function CardCategoryChip({
  category,
  className,
}: {
  category?: UserCardCategorySnippet | null | undefined
  /** Extra Tailwind classes (layout like `max-w-*`, `truncate`). */
  className?: string
}) {
  const raw = typeof category?.name === 'string' ? category.name.trim() : ''
  if (raw === '') return null
  const base =
    'inline-flex max-w-full truncate rounded-md border border-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_40%,transparent)] bg-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_12%,transparent)] px-2 py-0.5 text-[10px] font-semibold tracking-wide text-(--tgui--text_color)'
  return (
    <span className={[base, className].filter(Boolean).join(' ')} title="Полка">
      {raw}
    </span>
  )
}
