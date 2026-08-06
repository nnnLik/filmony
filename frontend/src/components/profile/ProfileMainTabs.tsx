import { SegmentedControl } from '../ui/SegmentedControl'

export type ProfileMainTab = 'movies' | 'stats'

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
      gridColsClassName="grid-cols-2"
      className={className}
      segments={[
        { value: 'movies', label: 'Карточки' },
        { value: 'stats', label: 'Статистика' },
      ]}
    />
  )
}
