import { SegmentedControl } from '../ui/SegmentedControl'

export type ProfileMainTab = 'movies' | 'posts' | 'stats'

type ProfileMainTabsProps = {
  value: ProfileMainTab
  onChange: (tab: ProfileMainTab) => void
  className?: string
}

export function ProfileMainTabs({ value, onChange, className }: ProfileMainTabsProps) {
  return (
    <SegmentedControl
      value={value}
      onChange={onChange}
      ariaLabel="Раздел профиля"
      layout="grid"
      gridColsClassName="grid-cols-3"
      className={className}
      segments={[
        { value: 'movies', label: 'Карточки' },
        { value: 'posts', label: 'Посты' },
        { value: 'stats', label: 'Статистика' },
      ]}
    />
  )
}
