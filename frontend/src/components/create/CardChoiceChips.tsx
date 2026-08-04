import { CHIP_COLORS } from '../../lib/cardFormOptions'

export type CardChoiceChipsProps<T extends string> = {
  options: Array<{ value: T; label: string }>
  selected: T
  onSelect: (value: T) => void
}

export function CardChoiceChips<T extends string>({
  options,
  selected,
  onSelect,
}: CardChoiceChipsProps<T>) {
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {options.map((option, index) => {
        const isSelected = option.value === selected
        const color = CHIP_COLORS[index % CHIP_COLORS.length]
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onSelect(option.value)}
            className={`rounded-xl border px-3 py-2 text-xs font-medium transition active:scale-[0.99] ${
              isSelected
                ? 'border-(--tgui--link_color) ring-1 ring-(--tgui--link_color) shadow-[0_0_0_1px_color-mix(in_srgb,var(--tgui--link_color)_20%,transparent)]'
                : 'border-(--tgui--divider_color) opacity-90'
            } ${color}`}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
