import type { ProfileMoviesSegment } from '../../lib/profileMoviesSegment'
import type { ProfileMainTab } from './profileMainTab'

export type ProfileSection = 'rated' | 'watchlist' | 'stats'

export function profileSectionOf(
  mainTab: ProfileMainTab,
  moviesSegment: ProfileMoviesSegment,
): ProfileSection {
  return mainTab === 'stats' ? 'stats' : moviesSegment
}

type ProfileSectionTabsProps = {
  value: ProfileSection
  onChange: (section: ProfileSection) => void
  counts?: Partial<Record<ProfileSection, number>>
  /** Sticks the control right under the page header while scrolling. */
  sticky?: boolean
  className?: string
}

const SECTIONS: { value: ProfileSection; label: string }[] = [
  { value: 'rated', label: 'Оценённые' },
  { value: 'watchlist', label: 'Позже' },
  { value: 'stats', label: 'Статистика' },
]

export function ProfileSectionTabs({
  value,
  onChange,
  counts,
  sticky = false,
  className,
}: ProfileSectionTabsProps) {
  return (
    <div
      className={`${
        sticky
          ? 'sticky top-[var(--filmony-page-header-h,52px)] z-10 -mx-4 bg-[color-mix(in_srgb,var(--tgui--bg_color)_88%,transparent)] px-4 py-2 backdrop-blur-md'
          : ''
      } ${className ?? ''}`}
    >
      <div
        className="flex gap-1 rounded-full bg-(--tgui--secondary_bg_color) p-1"
        role="tablist"
        aria-label="Раздел профиля"
      >
        {SECTIONS.map((section) => {
          const selected = value === section.value
          const count = counts?.[section.value]
          return (
            <button
              key={section.value}
              type="button"
              role="tab"
              aria-selected={selected}
              className={`flex min-w-0 flex-1 items-center justify-center gap-1.5 rounded-full px-2 py-2 text-[13px] font-medium transition-colors ${
                selected
                  ? 'bg-(--tgui--bg_color) text-(--tgui--text_color) shadow-sm'
                  : 'text-(--tgui--hint_color)'
              }`}
              onClick={() => onChange(section.value)}
            >
              <span className="truncate">{section.label}</span>
              {typeof count === 'number' && count > 0 ? (
                <span
                  className={`shrink-0 text-[11px] tabular-nums ${
                    selected
                      ? 'text-[color-mix(in_srgb,var(--filmony-mint,#5eead4)_75%,var(--tgui--text_color))]'
                      : 'text-(--tgui--hint_color)'
                  }`}
                >
                  {count}
                </span>
              ) : null}
            </button>
          )
        })}
      </div>
    </div>
  )
}
